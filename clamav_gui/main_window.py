"""Main window for the ClamAV GUI application."""
import os
import subprocess
import logging
import time
from pathlib import Path
from datetime import datetime
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QStatusBar, QProgressBar, QSizePolicy, QMenuBar, QMenu, QPushButton,
                             QDialog, QTextEdit, QPlainTextEdit, QComboBox, QLineEdit, QCheckBox, QGroupBox,
                             QScrollArea, QFrame, QSplitter, QToolBar, QStyle, QInputDialog,
                             QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem, QHeaderView,
                             QAbstractItemView, QTableWidget, QTableWidgetItem, QToolButton, QStyleFactory,
                             QMessageBox, QFileDialog)
from PySide6.QtCore import (QThread, Signal, QObject, QUrl, QProcess, QTimer, QSettings, 
                           QPoint, QByteArray, QBuffer, QIODevice, QProcessEnvironment, 
                           QStandardPaths, Slot)
from PySide6.QtGui import (QIcon, QPixmap, QFont, QColor, QTextCursor, QDesktopServices, 
                        QAction, QKeySequence, QTextCharFormat, QTextDocument, QTextFormat, 
                        QSyntaxHighlighter, QTextBlockUserData, QTextBlock, QPainter, QPalette, 
                        QFontMetrics, QGuiApplication, QClipboard, QImage, QMovie, QRegion)
from clamav_gui.ui.updates_ui import check_for_updates
from clamav_gui.ui.settings import AppSettings
from clamav_gui.ui.help import HelpDialog
from clamav_gui.ui.menu import ClamAVMenuBar
from clamav_gui.ui.status_tab import StatusTab
from clamav_gui.ui.conf_editor_tab import ConfigEditorTab
from clamav_gui.ui.home_tab import HomeTab
from clamav_gui.ui.advanced_dialogs import NetworkPathDialog, MLDetectionDialog, SmartScanningDialog
from clamav_gui.utils.virus_db import VirusDBUpdater

# Import language manager
from clamav_gui.lang.lang_manager import SimpleLanguageManager

# Import ClamAV validator
from clamav_gui.utils.clamav_validator import ClamAVValidator

# Import ClamAV manager for integrated scanning
from clamav_gui.utils.clamav_integration import ClamAVManager

# Import fallback manager for robust integration
from clamav_gui.utils.clamav_fallback_manager import ClamAVFallbackManager

# Import scan report generator
from clamav_gui.utils.scan_report import ScanReportGenerator

# Import quarantine manager
from clamav_gui.utils.quarantine_manager import QuarantineManager

# Import enhanced database updater
from clamav_gui.utils.enhanced_db_updater import EnhancedVirusDBUpdater, EnhancedUpdateThread

# Import scan thread for file scanning
from clamav_gui.utils.scan_thread import ScanThread

# Import hash database for smart scanning
from clamav_gui.utils.hash_database import HashDatabase

# Import advanced reporting for scan analytics
from clamav_gui.utils.advanced_reporting import AdvancedReporting

# Optional ML imports (only if needed and available)
_ML_AVAILABLE = True
try:
    from clamav_gui.utils.ml_threat_detector import MLThreatDetector, MLSandboxAnalyzer
except ImportError as e:
    logger.warning(f"ML threat detector not available: {e}")
    _ML_AVAILABLE = False

# Import sandbox analyzer
from clamav_gui.utils.sandbox_analyzer import SandboxAnalyzer

# Setup logger
logger = logging.getLogger(__name__)

from clamav_gui.ui.UI import ClamAVMainWindow

class ClamAVGUI(ClamAVMainWindow):
    """Main window for the ClamAV GUI application."""
    
    def __init__(self, lang_manager=None, parent=None):
        """Initialize the main window.
        
        Args:
            lang_manager: Instance of SimpleLanguageManager for translations
            parent: Parent widget
        """
        super().__init__(lang_manager, parent)
        self.settings = AppSettings()
        self.process = None
        self.scan_thread = None
        self.virus_db_updater = EnhancedVirusDBUpdater()
        self.hash_database = HashDatabase()
        self.clamav_validator = ClamAVValidator()
        self.scan_report_generator = ScanReportGenerator()
        # Quarantine manager will be initialized later after dependencies are set up
        # Note: ErrorRecoveryManager and NetworkErrorRecovery classes don't exist yet
        # self.error_recovery = ErrorRecoveryManager()
        # self.network_recovery = NetworkErrorRecovery()
        self.advanced_reporting = AdvancedReporting()

        # Initialize ClamAV manager for integrated scanning
        try:
            self.clamav_manager = ClamAVManager()
            logger.info("ClamAV manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ClamAV manager: {e}")
            self.clamav_manager = None

        # Initialize fallback manager for robust integration
        try:
            self.fallback_manager = ClamAVFallbackManager()
            logger.info("ClamAV fallback manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ClamAV fallback manager: {e}")
            self.fallback_manager = None

        # Initialize ML components only if available
        self.ml_detector = None
        self.ml_sandbox_analyzer = None
        if _ML_AVAILABLE:
            try:
                self.ml_detector = MLThreatDetector()
                self.ml_sandbox_analyzer = MLSandboxAnalyzer()
                logger.info("ML threat detector initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize ML components: {e}")
                self.ml_detector = None
                self.ml_sandbox_analyzer = None

        self.sandbox_analyzer = SandboxAnalyzer()
        
        self.lang_manager = lang_manager or SimpleLanguageManager()
        
        # Connect language changed signal
        if hasattr(self.lang_manager, 'language_changed'):
            self.lang_manager.language_changed.connect(self.retranslate_ui)
        # Set up the main window
        self.setWindowTitle(self.tr("ClamAV GUI"))
        self.resize(800, 680)
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setWindowIcon(QIcon("assets/icon.ico"))
                
        # Set application icon
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                logger.warning(f"Icon not found at: {icon_path}")
        except Exception as e:
            logger.warning(f"Failed to load application icon: {e}")
        
        # Initialize menu attributes
        self.file_menu = None
        self.tools_menu = None
        self.help_menu = None
        self.language_menu = None
        
        # Check quarantine manager status and show warning if needed
        QTimer.singleShot(1000, self.check_quarantine_manager_status)  # Delay to allow UI to load

    def get_scanner_type(self):
        """Get the current scanner type from settings."""
        if hasattr(self, 'current_settings') and self.current_settings:
            return self.current_settings.get('scanner_type', 'integrated')
        return 'integrated'  # Default to integrated scanner

    def is_integrated_scanner(self):
        """Check if integrated scanner is selected."""
        return self.get_scanner_type() == 'integrated'

    def is_clamav_scanner(self):
        """Check if ClamAV scanner is selected."""
        return self.get_scanner_type() == 'clamav'

    def reinitialize_quarantine_manager(self):
        """Reinitialize the quarantine manager with fallback if needed."""
        try:
            # Try to initialize with default directory
            self.quarantine_manager = QuarantineManager()
            logger.info("Quarantine manager reinitialized successfully")
            return True
        except Exception as e:
            logger.warning(f"Failed to reinitialize quarantine manager: {e}")
            try:
                # Try with fallback directory
                app_dir = os.path.dirname(os.path.dirname(__file__))
                fallback_dir = os.path.join(app_dir, 'quarantine')
                self.quarantine_manager = QuarantineManager(fallback_dir)
                logger.info(f"Quarantine manager reinitialized with fallback: {fallback_dir}")
                return True
            except Exception as e2:
                logger.error(f"Failed to reinitialize quarantine manager with fallback: {e2}")
                self.quarantine_manager = None
                return False
    
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
        self.home_tab = self.create_home_tab()
        self.scan_tab = self.create_scan_tab()
        self.email_scan_tab = self.create_email_scan_tab()
        self.virus_db_tab = self.create_virus_db_tab()
        self.update_tab = self.create_update_tab()
        self.settings_tab = self.create_settings_tab()
        self.quarantine_tab = self.create_quarantine_tab()
        self.config_editor_tab = self.create_config_editor_tab()
        self.network_scan_tab = self.create_network_scan_tab()
        self.ml_detection_tab = self.create_ml_detection_tab()
        self.smart_scanning_tab = self.create_smart_scanning_tab()
        self.status_tab = StatusTab(self)
        
        self.tabs.addTab(self.home_tab, self.tr("Home"))
        self.tabs.addTab(self.scan_tab, self.tr("Scan"))
        self.tabs.addTab(self.email_scan_tab, self.tr("Email Scan"))
        self.tabs.addTab(self.virus_db_tab, self.tr("VirusDB"))
        self.tabs.addTab(self.update_tab, self.tr("Update"))
        self.tabs.addTab(self.settings_tab, self.tr("Settings"))
        self.tabs.addTab(self.quarantine_tab, self.tr("Quarantine"))
        self.tabs.addTab(self.config_editor_tab, self.tr("Config Editor"))
        self.tabs.addTab(self.network_scan_tab, self.tr("Network Scan"))
        self.tabs.addTab(self.ml_detection_tab, self.tr("ML Detection"))
        self.tabs.addTab(self.smart_scanning_tab, self.tr("Smart Scanning"))
        self.tabs.addTab(self.status_tab, self.tr("Status"))
        
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
        try:
            mb = self.menuBar()
            logger.info(f"Menu bar set: exists={mb is not None}")
            if mb is not None:
                menus = mb.findChildren(QMenu)
                titles = [m.title() for m in menus]
                logger.info(f"Menu count={len(menus)} titles={titles}")
        except Exception as e:
            logger.warning(f"Menu bar diagnostic error: {e}")
        
        # Set the language manager for the menu bar
        if hasattr(self, 'lang_manager') and self.lang_manager is not None:
            self.menu_bar.set_language_manager(self.lang_manager)
        
        # Connect menu signals
        self.menu_bar.help_requested.connect(self.show_help)
        self.menu_bar.about_requested.connect(self.show_about)
        self.menu_bar.sponsor_requested.connect(self.show_sponsor)
        self.menu_bar.update_check_requested.connect(lambda: self.check_for_updates(force_check=True))
        
    def check_quarantine_manager_status(self):
        """Check if quarantine manager is properly initialized and show status."""
        if not self.quarantine_manager:
            # Try to reinitialize
            if self.reinitialize_quarantine_manager():
                QMessageBox.information(
                    self,
                    self.tr("Quarantine Manager Status"),
                    self.tr("Quarantine manager has been successfully initialized with a fallback directory.\n\n"
                           "Quarantine functionality is now available.")
                )
                return True
            else:
                QMessageBox.information(
                    self,
                    self.tr("Quarantine Manager Status"),
                    self.tr("The quarantine manager could not be initialized.\n\n"
                           "This may be due to:\n"
                           "• Permission issues with the Documents folder\n"
                           "• Insufficient disk space\n"
                           "• System restrictions\n\n"
                           "Quarantine functionality will be limited until this issue is resolved.")
                )
                return False
        return True

    def start_menu_diagnostics(self):
        self._menu_diag_count = 0
        self._menu_diag_timer = QTimer(self)
        def _tick():
            try:
                mb = self.menuBar()
                exists = mb is not None
                titles = []
                actions = 0
                if mb is not None:
                    menus = mb.findChildren(QMenu)
                    titles = [m.title() for m in menus]
                    actions = sum(len(m.actions()) for m in menus)
                logger.info(f"Menu diag: exists={exists} menus={len(titles)} actions={actions} titles={titles}")
            except Exception as e:
                logger.warning(f"Menu diag error: {e}")
            finally:
                self._menu_diag_count += 1
                if self._menu_diag_count >= 8:
                    self._menu_diag_timer.stop()
        self._menu_diag_timer.timeout.connect(_tick)
        self._menu_diag_timer.start(2000)
    
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
        """Set up the language selection menu with only available languages."""
        if not hasattr(self, 'lang_manager') or not self.lang_manager:
            return
            
        # Get the language menu from the menu bar if not already set
        if not hasattr(self, 'language_menu') or self.language_menu is None:
            if hasattr(self, 'menu_bar') and hasattr(self.menu_bar, 'language_menu'):
                self.language_menu = self.menu_bar.language_menu
            else:
                return
                
        # Clear existing actions
        if self.language_menu is not None:
            self.language_menu.clear()
            
            # Make the menu exclusive (like a radio button group)
            self.language_menu.setToolTipsVisible(True)
            
            # Add only available languages that have translations
            for lang_code, lang_name in self.lang_manager.available_languages.items():
                # Only add languages that have actual translations
                if hasattr(self.lang_manager, 'is_language_available') and \
                   self.lang_manager.is_language_available(lang_code):
                    action = self.language_menu.addAction(lang_name, self.change_language)
                    action.setCheckable(True)
                    action.setData(lang_code)
                    
                    # Check current language
                    if hasattr(self.lang_manager, 'current_lang') and \
                       lang_code == self.lang_manager.current_lang:
                        action.setChecked(True)
                
                # Check current language
                if lang_code == self.lang_manager.current_lang:
                    action.setChecked(True)
    
    def change_language(self):
        """Change the application language."""
        # Initialize action to None to ensure it's always defined
        action = None
        try:
            action = self.sender()
            if not action or not hasattr(self, 'lang_manager'):
                return
                
            lang_code = action.data()
            if lang_code and self.lang_manager.set_language(lang_code):
                logger.info(f"Language changed to {lang_code}")
                
                # Save language preference
                if not hasattr(self, 'current_settings'):
                    self.current_settings = {}
                self.current_settings['language'] = lang_code
                self.settings.save_settings(self.current_settings)
        except Exception as e:
            logger.error(f"Error in change_language: {e}")
    
    def retranslate_ui(self, language_code=None):
        """Retranslate the UI when language changes.
        
        Args:
            language_code: Optional language code to set (default: None, uses current language)
        """
        if not hasattr(self, 'lang_manager') or not self.lang_manager:
            return
            
        try:
            # Update window title
            self.setWindowTitle(self.tr("ClamAV GUI"))
            
            # Update menu bar if it exists
            if hasattr(self, 'menu_bar'):
                # Update menu titles if they exist
                if hasattr(self, 'file_menu') and self.file_menu:
                    self.file_menu.setTitle(self.tr("&File"))
                if hasattr(self, 'tools_menu') and self.tools_menu:
                    self.tools_menu.setTitle(self.tr("&Tools"))
                if hasattr(self, 'help_menu') and self.help_menu:
                    self.help_menu.setTitle(self.tr("&Help"))
                if hasattr(self, 'language_menu') and self.language_menu:
                    self.language_menu.setTitle(self.tr("&Language"))
            
            # Update menu actions if they exist
            if hasattr(self, 'exit_action') and self.exit_action:
                self.exit_action.setText(self.tr("E&xit"))
            if hasattr(self, 'check_updates_action') and self.check_updates_action:
                self.check_updates_action.setText(self.tr("Check for &Updates..."))
            if hasattr(self, 'help_action') and self.help_action:
                self.help_action.setText(self.tr("&Help"))
            if hasattr(self, 'about_action') and self.about_action:
                self.about_action.setText(self.tr("&About"))
            if hasattr(self, 'sponsor_action') and self.sponsor_action:
                self.sponsor_action.setText(self.tr("&Support the Project"))
            
            # Update tab names
            if hasattr(self, 'tabs'):
                self.tabs.setTabText(0, self.tr("Home"))
                self.tabs.setTabText(1, self.tr("Scan"))
                self.tabs.setTabText(2, self.tr("Email Scan"))
                self.tabs.setTabText(3, self.tr("VirusDB"))
                self.tabs.setTabText(4, self.tr("Update"))
                self.tabs.setTabText(5, self.tr("Settings"))
                self.tabs.setTabText(6, self.tr("Quarantine"))
                self.tabs.setTabText(7, self.tr("Config Editor"))
                self.tabs.setTabText(8, self.tr("Network Scan"))
                self.tabs.setTabText(9, self.tr("ML Detection"))
                self.tabs.setTabText(10, self.tr("Smart Scanning"))
                self.tabs.setTabText(11, self.tr("Status"))
            
            # Update status bar
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(self.tr("Ready"))
            
        except Exception as e:
            logger.error(f"Error retranslating UI: {e}")
    
    def check_for_updates(self, force_check=False):
        """Check for application updates."""
        from . import __version__
        check_for_updates(parent=self, current_version=__version__, force_check=force_check)
    
    def create_home_tab(self):
        """Create the home tab using HomeTab class."""
        try:
            return HomeTab(self)
        except ImportError as e:
            logger.warning(f"Could not import HomeTab: {e}")
            # Fallback to simple home tab
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Home tab not available")))
            return tab
    
    def create_scan_tab(self):
        """Create the scan tab using ScanTab class."""
        try:
            from clamav_gui.ui.scan_tab import ScanTab
            return ScanTab(self)
        except ImportError as e:
            logger.warning(f"Could not import ScanTab: {e}")
            # Fallback to simple scan tab
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Scan tab not available")))
            return tab
    
    def create_email_scan_tab(self):
        """Create the email scanning tab using EmailScanTab class."""
        try:
            from clamav_gui.ui.email_scan_tab import EmailScanTab
            return EmailScanTab(self)
        except ImportError as e:
            logger.warning(f"Could not import EmailScanTab: {e}")
            # Fallback to simple email scan tab
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Email Scan tab not available")))
            return tab
    
    def create_quarantine_tab(self):
        """Create the quarantine tab using QuarantineTab class."""
        try:
            from clamav_gui.ui.quarantine_tab import QuarantineTab
            tab = QuarantineTab(self)
            # Set the quarantine manager reference
            if hasattr(self, 'quarantine_manager') and self.quarantine_manager:
                tab.set_quarantine_manager(self.quarantine_manager)
            return tab
        except ImportError as e:
            logger.warning(f"Could not import QuarantineTab: {e}")
            # Fallback to simple quarantine tab
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Quarantine tab not available")))
            return tab
    
    def create_smart_scanning_tab(self):
        """Create the smart scanning tab using SmartScanningTab class."""
        try:
            from clamav_gui.ui.smart_scanning_tab import SmartScanningTab
            return SmartScanningTab(self)
        except ImportError as e:
            logger.warning(f"Could not import SmartScanningTab: {e}")
            # Fallback to simple smart scanning tab
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Smart Scanning tab not available")))
            return tab
    
    def refresh_quarantine_stats(self):
        """Refresh the quarantine statistics display."""
        try:
            if not self.quarantine_manager:
                self.quarantine_stats_text.setPlainText("Quarantine manager not initialized")
                return

            stats = self.quarantine_manager.get_quarantine_stats()
            
            stats_text = f"""
Quarantine Statistics:
====================

Total quarantined files: {stats.get('total_quarantined', 0)}
Total size: {stats.get('total_size_mb', 0):.2f} MB

Threat types found:
{chr(10).join(f"  • {threat}" for threat in stats.get('threat_types', [])) if stats.get('threat_types') else "  None"}

Last activity:
  Newest file: {stats.get('newest_file') or 'N/A'}
  Oldest file: {stats.get('oldest_file') or 'N/A'}
"""
            self.quarantine_stats_text.setPlainText(stats_text.strip())
            
        except Exception as e:
            error_msg = f"Error loading quarantine statistics: {str(e)}"
            logger.error(error_msg)
            self.quarantine_stats_text.setPlainText(error_msg)
    
    def refresh_quarantine_files(self):
        """Refresh the list of quarantined files."""
        try:
            if not self.quarantine_manager:
                self.quarantine_files_list.clear()
                self.quarantine_files_list.addItem("Quarantine manager not initialized")
                return

            self.quarantine_files_list.clear()
            quarantined_files = self.quarantine_manager.list_quarantined_files()
            
            if not quarantined_files:
                self.quarantine_files_list.addItem(self.tr("No quarantined files"))
                return
                
            for file_info in quarantined_files:
                filename = file_info.get('original_filename', 'Unknown')
                threat = file_info.get('threat_name', 'Unknown')
                size = file_info.get('file_size', 0)
                item_text = f"{filename} - {threat} ({size} bytes)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, file_info)
                self.quarantine_files_list.addItem(item)
                
        except Exception as e:
            self.quarantine_files_list.clear()
            self.quarantine_files_list.addItem(f"Error loading quarantined files: {str(e)}")
    
    def restore_selected_file(self):
        """Restore the selected quarantined file."""
        current_item = self.quarantine_files_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select a file to restore"))
            return
        
        file_info = current_item.data(Qt.UserRole)
        if not file_info:
            return
        
        filename = file_info.get('original_filename', 'Unknown')
        
        reply = QMessageBox.question(
            self, self.tr("Restore File"),
            self.tr(f"Are you sure you want to restore '{filename}'?\n\n"
                   "Warning: This file was detected as infected and may be dangerous."),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Get file ID from the item data
            file_id = None
            for key, value in file_info.items():
                if key.startswith('file_hash') or (isinstance(key, str) and len(key) > 10 and key.replace('_', '').isalnum()):
                    # Try to find a reasonable file ID
                    file_id = key
                    break
            
            if not file_id and 'quarantined_path' in file_info:
                # Fallback: try to extract file ID from quarantined path
                quarantined_path = file_info['quarantined_path']
                basename = os.path.basename(quarantined_path)
                # Extract timestamp_hash_filename format
                parts = basename.split('_', 2)
                if len(parts) >= 2:
                    file_id = f"{parts[1]}_{parts[0]}"  # hash_timestamp format
            
            if not file_id:
                QMessageBox.critical(
                    self, self.tr("Restore Failed"),
                    self.tr("Could not determine file ID for restoration. The file may be corrupted.")
                )
                return
            
            # Perform the restore operation
            success, message = self.quarantine_manager.restore_file(file_id)
            
            if success:
                QMessageBox.information(
                    self, self.tr("Restore Successful"),
                    self.tr(f"File '{filename}' has been successfully restored.\n\n{message}")
                )
                # Refresh the quarantine lists
                self.refresh_quarantine_stats()
                self.refresh_quarantine_files()
            else:
                QMessageBox.critical(
                    self, self.tr("Restore Failed"),
                    self.tr(f"Failed to restore file '{filename}':\n\n{message}")
                )
    
    def delete_selected_file(self):
        """Delete the selected quarantined file."""
        current_item = self.quarantine_files_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select a file to delete"))
            return
        
        file_info = current_item.data(Qt.UserRole)
        if not file_info:
            return
        
        filename = file_info.get('original_filename', 'Unknown')
        
        reply = QMessageBox.question(
            self, self.tr("Delete File"),
            self.tr(f"Are you sure you want to permanently delete '{filename}'?\n\n"
                   "This action cannot be undone."),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Get file ID from the item data
            file_id = None
            for key, value in file_info.items():
                if key.startswith('file_hash') or (isinstance(key, str) and len(key) > 10 and key.replace('_', '').isalnum()):
                    # Try to find a reasonable file ID
                    file_id = key
                    break
            
            if not file_id and 'quarantined_path' in file_info:
                # Fallback: try to extract file ID from quarantined path
                quarantined_path = file_info['quarantined_path']
                basename = os.path.basename(quarantined_path)
                # Extract timestamp_hash_filename format
                parts = basename.split('_', 2)
                if len(parts) >= 2:
                    file_id = f"{parts[1]}_{parts[0]}"  # hash_timestamp format
            
            if not file_id:
                QMessageBox.critical(
                    self, self.tr("Delete Failed"),
                    self.tr("Could not determine file ID for deletion. The file may be corrupted.")
                )
                return
            
            # Perform the delete operation
            success, message = self.quarantine_manager.delete_quarantined_file(file_id)
            
            if success:
                QMessageBox.information(
                    self, self.tr("Delete Successful"),
                    self.tr(f"File '{filename}' has been permanently deleted.\n\n{message}")
                )
                # Refresh the quarantine lists
                self.refresh_quarantine_stats()
                self.refresh_quarantine_files()
            else:
                QMessageBox.critical(
                    self, self.tr("Delete Failed"),
                    self.tr(f"Failed to delete file '{filename}':\n\n{message}")
                )
    
    def restore_selected_files(self):
        """Restore multiple selected quarantined files."""
        selected_items = self.quarantine_files_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select files to restore"))
            return
        
        if len(selected_items) == 1:
            # Single file - use existing method
            self.restore_selected_file()
            return
        
        # Multiple files
        file_list = []
        for item in selected_items:
            file_info = item.data(Qt.UserRole)
            if file_info:
                filename = file_info.get('original_filename', 'Unknown')
                file_list.append(filename)
        
        reply = QMessageBox.question(
            self, self.tr("Restore Multiple Files"),
            self.tr(f"Are you sure you want to restore {len(selected_items)} files?\n\n"
                   "Files to restore:\n" + "\n".join(f"• {name}" for name in file_list[:5]) +
                   (f"\n... and {len(file_list) - 5} more" if len(file_list) > 5 else "") +
                   "\n\nWarning: These files were detected as infected and may be dangerous."),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success_count = 0
            error_count = 0
            errors = []
            
            for item in selected_items:
                file_info = item.data(Qt.UserRole)
                if not file_info:
                    continue
                
                # Get file ID
                file_id = self._get_file_id_from_info(file_info)
                if not file_id:
                    error_count += 1
                    errors.append(f"Could not determine ID for {file_info.get('original_filename', 'Unknown')}")
                    continue
                
                success, message = self.quarantine_manager.restore_file(file_id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{file_info.get('original_filename', 'Unknown')}: {message}")
            
            # Show results
            result_msg = f"Restored {success_count} files successfully."
            if error_count > 0:
                result_msg += f"\n\nFailed to restore {error_count} files:"
                result_msg += "\n" + "\n".join(errors[:3])  # Show first 3 errors
                if error_count > 3:
                    result_msg += f"\n... and {error_count - 3} more errors"
            
            if success_count > 0:
                QMessageBox.information(self, self.tr("Restore Complete"), result_msg)
                self.refresh_quarantine_stats()
                self.refresh_quarantine_files()
            else:
                QMessageBox.critical(self, self.tr("Restore Failed"), result_msg)
    
    def delete_selected_files(self):
        """Delete multiple selected quarantined files."""
        selected_items = self.quarantine_files_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select files to delete"))
            return
        
        if len(selected_items) == 1:
            # Single file - use existing method
            self.delete_selected_file()
            return
        
        # Multiple files
        file_list = []
        for item in selected_items:
            file_info = item.data(Qt.UserRole)
            if file_info:
                filename = file_info.get('original_filename', 'Unknown')
                file_list.append(filename)
        
        reply = QMessageBox.question(
            self, self.tr("Delete Multiple Files"),
            self.tr(f"Are you sure you want to permanently delete {len(selected_items)} files?\n\n"
                   "Files to delete:\n" + "\n".join(f"• {name}" for name in file_list[:5]) +
                   (f"\n... and {len(file_list) - 5} more" if len(file_list) > 5 else "") +
                   "\n\nThis action cannot be undone."),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success_count = 0
            error_count = 0
            errors = []
            
            for item in selected_items:
                file_info = item.data(Qt.UserRole)
                if not file_info:
                    continue
                
                # Get file ID
                file_id = self._get_file_id_from_info(file_info)
                if not file_id:
                    error_count += 1
                    errors.append(f"Could not determine ID for {file_info.get('original_filename', 'Unknown')}")
                    continue
                
                success, message = self.quarantine_manager.delete_quarantined_file(file_id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{file_info.get('original_filename', 'Unknown')}: {message}")
            
            # Show results
            result_msg = f"Deleted {success_count} files successfully."
            if error_count > 0:
                result_msg += f"\n\nFailed to delete {error_count} files:"
                result_msg += "\n" + "\n".join(errors[:3])  # Show first 3 errors
                if error_count > 3:
                    result_msg += f"\n... and {error_count - 3} more errors"
            
            if success_count > 0:
                QMessageBox.information(self, self.tr("Delete Complete"), result_msg)
                self.refresh_quarantine_stats()
                self.refresh_quarantine_files()
            else:
                QMessageBox.critical(self, self.tr("Delete Failed"), result_msg)
    
    def restore_all_files(self):
        """Restore all quarantined files."""
        quarantined_files = self.quarantine_manager.list_quarantined_files()
        if not quarantined_files:
            QMessageBox.information(self, self.tr("No Files"), self.tr("No files in quarantine to restore"))
            return
        
        reply = QMessageBox.question(
            self, self.tr("Restore All Files"),
            self.tr(f"Are you sure you want to restore all {len(quarantined_files)} quarantined files?\n\n"
                   "Warning: These files were detected as infected and may be dangerous."),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success_count = 0
            error_count = 0
            errors = []
            
            for file_info in quarantined_files:
                # Get file ID
                file_id = self._get_file_id_from_info(file_info)
                if not file_id:
                    error_count += 1
                    errors.append(f"Could not determine ID for {file_info.get('original_filename', 'Unknown')}")
                    continue
                
                success, message = self.quarantine_manager.restore_file(file_id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{file_info.get('original_filename', 'Unknown')}: {message}")
            
            # Show results
            result_msg = f"Restored {success_count} files successfully."
            if error_count > 0:
                result_msg += f"\n\nFailed to restore {error_count} files."
            
            QMessageBox.information(self, self.tr("Restore Complete"), result_msg)
            self.refresh_quarantine_stats()
            self.refresh_quarantine_files()
    
    def delete_all_files(self):
        """Delete all quarantined files."""
        quarantined_files = self.quarantine_manager.list_quarantined_files()
        if not quarantined_files:
            QMessageBox.information(self, self.tr("No Files"), self.tr("No files in quarantine to delete"))
            return
        
        reply = QMessageBox.question(
            self, self.tr("Delete All Files"),
            self.tr(f"Are you sure you want to permanently delete all {len(quarantined_files)} quarantined files?\n\n"
                   "This action cannot be undone."),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success_count = 0
            error_count = 0
            errors = []
            
            for file_info in quarantined_files:
                # Get file ID
                file_id = self._get_file_id_from_info(file_info)
                if not file_id:
                    error_count += 1
                    errors.append(f"Could not determine ID for {file_info.get('original_filename', 'Unknown')}")
                    continue
                
                success, message = self.quarantine_manager.delete_quarantined_file(file_id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{file_info.get('original_filename', 'Unknown')}: {message}")
            
            # Show results
            result_msg = f"Deleted {success_count} files successfully."
            if error_count > 0:
                result_msg += f"\n\nFailed to delete {error_count} files."
            
            QMessageBox.information(self, self.tr("Delete Complete"), result_msg)
            self.refresh_quarantine_stats()
            self.refresh_quarantine_files()
    
    def cleanup_old_files(self):
        """Clean up quarantined files older than 30 days."""
        reply = QMessageBox.question(
            self, self.tr("Cleanup Old Files"),
            self.tr("This will permanently delete all quarantined files older than 30 days.\n\n"
                   "Do you want to continue?"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            deleted_count, message = self.quarantine_manager.cleanup_old_files(30)
            
            QMessageBox.information(
                self, self.tr("Cleanup Complete"),
                self.tr(f"Cleanup completed.\n\n{message}")
            )
            
            self.refresh_quarantine_stats()
            self.refresh_quarantine_files()
    
    def _get_file_id_from_info(self, file_info):
        """Extract file ID from file info dictionary."""
        # Try multiple methods to get file ID
        for key, value in file_info.items():
            if key.startswith('file_hash') or (isinstance(key, str) and len(key) > 10 and key.replace('_', '').isalnum()):
                return key
        
        if 'quarantined_path' in file_info:
            # Fallback: try to extract file ID from quarantined path
            quarantined_path = file_info['quarantined_path']
            basename = os.path.basename(quarantined_path)
            # Extract timestamp_hash_filename format
            parts = basename.split('_', 2)
            if len(parts) >= 2:
                return f"{parts[1]}_{parts[0]}"  # hash_timestamp format
        
        return None
    
    def export_quarantine_list(self):
        """Export the quarantine list to a file."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export Quarantine List"),
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_name:
            return
        
        if not file_name.lower().endswith('.json'):
            file_name += '.json'
        
        success = self.quarantine_manager.export_quarantine_list(file_name)
        
        if success:
            QMessageBox.information(
                self, self.tr("Export Complete"),
                self.tr(f"Quarantine list exported successfully:\n{file_name}")
            )
        else:
            QMessageBox.critical(
                self, self.tr("Export Failed"),
                self.tr("Failed to export quarantine list")
            )
    
    def create_config_editor_tab(self):
        """Create the config editor tab using ConfigEditorTab class."""
        try:
            tab = ConfigEditorTab(self)
            return tab
        except ImportError as e:
            logger.warning(f"Could not import ConfigEditorTab: {e}")
            # Fallback to simple config editor tab
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Config Editor tab not available")))
            return tab

    def create_network_scan_tab(self):
        """Create the network scan tab using NetworkScanTab class."""
        try:
            from clamav_gui.ui.net_scan_tab import NetworkScanTab
            return NetworkScanTab(self)
        except ImportError as e:
            logger.warning(f"Could not import NetworkScanTab: {e}")
            # Fallback to simple network scan tab
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Network Scan tab not available")))
            return tab

    def create_virus_db_tab(self):
        """Create the virus database tab using VirusDBTab class."""
        try:
            from clamav_gui.ui.virus_db_tab import VirusDBTab
            return VirusDBTab(self)
        except ImportError as e:
            logger.warning(f"Could not import VirusDBTab: {e}")
            # Fallback to simple virus database tab
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(QLabel(self.tr("Virus Database tab not available")))
            return tab

    # Add the rest of the original methods here
    def browse_target(self):
        """Open a file dialog to select a file or directory to scan."""
        # First try to get a regular directory
        target = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"))

        if target:
            self.target_input.setText(target)
            return

        # If no directory selected, check if user wants to enter UNC path manually
        unc_path, ok = QInputDialog.getText(
            self,
            self.tr("Network Path"),
            self.tr("Enter UNC path (e.g., \\\\server\\share):"),
            QLineEdit.Normal,
            ""
        )

        if ok and unc_path.strip():
            # Validate UNC path format
            if not unc_path.strip().startswith('\\\\'):
                QMessageBox.warning(
                    self,
                    self.tr("Invalid Path"),
                    self.tr("Network paths must start with \\\\. Example: \\\\server\\share")
                )
                return

            self.target_input.setText(unc_path.strip())
    
    def start_scan(self):
        """Start the ClamAV scan using selected scanner type."""
        target = self.target_input.text()
        if not target:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Please select a target to scan"))
            return

        # Get the selected scanner type from settings
        scanner_type = self.current_settings.get('scanner_type', 'integrated')
        if hasattr(self, 'scanner_type_combo'):
            scanner_type = self.scanner_type_combo.currentData() or scanner_type

        # Check scanner availability based on type
        if scanner_type == 'integrated':
            if not self.clamav_manager or not self.clamav_manager.is_available():
                QMessageBox.critical(
                    self, self.tr("ClamAV Not Available"),
                    self.tr("Integrated ClamAV scanner is not available. Please ensure ClamAV is properly installed and configured, or switch to External Scanner mode.")
                )
                return
        elif scanner_type == 'external':
            # Check if clamscan is available for external scanning
            clamscan_path = self.current_settings.get('clamscan_path', 'clamscan')
            if clamscan_path and clamscan_path != 'clamscan':
                # Custom path provided
                if not os.path.exists(clamscan_path):
                    QMessageBox.critical(
                        self, self.tr("ClamAV Not Found"),
                        self.tr(f"External ClamAV scanner not found at: {clamscan_path}\n\nPlease check the ClamAV installation or update the path in Settings.")
                    )
                    return
            else:
                # Check if clamscan is in PATH
                try:
                    subprocess.run(['clamscan', '--version'], capture_output=True, check=True, timeout=5)
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    QMessageBox.critical(
                        self, self.tr("ClamAV Not Available"),
                        self.tr("External ClamAV scanner (clamscan) is not available.\n\n"
                               "To fix this issue:\n"
                               "1. Install ClamAV for Windows from the official website:\n"
                               "   https://www.clamav.net/downloads\n\n"
                               "2. Or install via Chocolatey (if available):\n"
                               "   choco install clamav\n\n"
                               "3. Or install via Scoop (if available):\n"
                               "   scoop install clamav\n\n"
                               "After installation, make sure clamscan is in your system PATH, "
                               "or update the ClamAV paths in Settings.")
                    )
                    return
        elif scanner_type == 'auto':
            # Auto-detect: prefer integrated if available, fallback to external
            if self.clamav_manager and self.clamav_manager.is_available():
                scanner_type = 'integrated'
            else:
                scanner_type = 'external'
                # Check external availability for auto mode
                clamscan_path = self.current_settings.get('clamscan_path', 'clamscan')
                if clamscan_path and clamscan_path != 'clamscan':
                    if not os.path.exists(clamscan_path):
                        QMessageBox.critical(
                            self, self.tr("ClamAV Not Available"),
                            self.tr("No ClamAV integration is available.\n\n"
                                   "To fix this issue:\n"
                                   "1. Install ClamAV for Windows from the official website:\n"
                                   "   https://www.clamav.net/downloads\n\n"
                                   "2. Or install via Chocolatey (if available):\n"
                                   "   choco install clamav\n\n"
                                   "3. Or install via Scoop (if available):\n"
                                   "   scoop install clamav\n\n"
                                   "After installation, make sure clamscan is in your system PATH, "
                                   "or update the ClamAV paths in Settings.")
                        )
                        return
                else:
                    try:
                        subprocess.run(['clamscan', '--version'], capture_output=True, check=True, timeout=5)
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                        QMessageBox.critical(
                            self, self.tr("ClamAV Not Available"),
                            self.tr("No ClamAV integration is available.\n\n"
                                   "To fix this issue:\n"
                                   "1. Install ClamAV for Windows from the official website:\n"
                                   "   https://www.clamav.net/downloads\n\n"
                                   "2. Or install via Chocolatey (if available):\n"
                                   "   choco install clamav\n\n"
                                   "3. Or install via Scoop (if available):\n"
                                   "   scoop install clamav\n\n"
                                   "After installation, make sure clamscan is in your system PATH, "
                                   "or update the ClamAV paths in Settings.")
                        )
                        return

        # Validate network path if it's a UNC path
        if target.startswith('\\\\'):
            from clamav_gui.utils.network_scanner import NetworkScanner
            network_scanner = NetworkScanner()
            is_valid, message = network_scanner.validate_network_path(target)

            if not is_valid:
                reply = QMessageBox.question(
                    self, self.tr("Network Path Issue"),
                    self.tr(f"Network path validation failed: {message}\n\n"
                           "Do you want to continue with the scan anyway?"),
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return

        # Show scanner type being used
        scanner_names = {
            'integrated': 'Direct ClamAV Integration',
            'external': 'External ClamAV Scanner',
            'auto': f'Auto-detected ({scanner_type})'
        }
        self.output.append(f"🔧 Using scanner: {scanner_names.get(scanner_type, scanner_type)}")

        # Prepare scan options
        scan_options = {
            'recursive': self.recursive_scan.isChecked(),
            'scan_archives': self.scan_archives.isChecked(),
            'scan_heuristics': self.heuristic_scan.isChecked(),
            'scan_pua': self.scan_pua.isChecked(),
            'enable_smart_scanning': self.enable_smart_scanning.isChecked()
        }

        # Get performance settings
        try:
            max_file_size = int(self.max_file_size.text()) if self.max_file_size.text() else 100
            max_scan_time = int(self.max_scan_time.text()) if self.max_scan_time.text() else 300
        except ValueError:
            max_file_size = 100
            max_scan_time = 300

        # Start the scan using the appropriate method
        try:
            # Clear output area
            self.output.clear()

            # Update UI
            self.scan_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.save_report_btn.setEnabled(False)

            # Initialize progress bar
            if hasattr(self, 'progress'):
                self.progress.setRange(0, 0)  # Animated mode initially
                self.progress.setValue(0)

            # Initialize scan results storage
            self.current_scan_results = []

            if scanner_type == 'integrated':
                # Use integrated scanner
                # Connect signals from ClamAV manager
                self.clamav_manager.scan_progress.connect(self.update_progress)
                self.clamav_manager.scan_output.connect(self.update_scan_output)
                self.clamav_manager.scan_stats.connect(self.update_scan_stats)
                self.clamav_manager.file_scanned.connect(self.on_file_scanned)

                # Define completion callback
                def on_scan_complete(success, message, files_scanned, threats_found):
                    self.scan_finished(success, message, files_scanned, threats_found)

                # Start the scan based on target type
                if os.path.isfile(target):
                    # Single file scan
                    self.clamav_manager.scan_files_async([target], on_scan_complete)
                elif os.path.isdir(target):
                    # Directory scan
                    self.clamav_manager.scan_directory_async(target, scan_options['recursive'], on_scan_complete)
                else:
                    # Network path or other
                    self.clamav_manager.scan_files_async([target], on_scan_complete)

            else:  # external or auto-detected external
                # Use external scanner (subprocess-based)
                # This would require implementing an external scanner class or modifying the existing scan thread
                # For now, fall back to the original subprocess method but with the scanner type awareness
                self._start_external_scan(target, scan_options, max_file_size, max_scan_time)

        except Exception as e:
            logger.error(f"Error starting scan: {e}")
            QMessageBox.critical(self, self.tr("Scan Error"),
                               self.tr(f"Failed to start scan: {str(e)}"))

            # Reset UI
            self.scan_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.save_report_btn.setEnabled(False)

    def _start_external_scan(self, target, scan_options, max_file_size, max_scan_time):
        """Start external scan using subprocess-based scanning."""
        # Get clamscan path from settings
        clamscan_path = self.current_settings.get('clamscan_path', 'clamscan')

        # Build command arguments
        cmd_args = []

        # Add basic options
        if scan_options['recursive']:
            cmd_args.append('-r')
        if scan_options['scan_heuristics']:
            cmd_args.append('--scan-heuristic')
        if scan_options['scan_pua']:
            cmd_args.append('--scan-pua')
        if scan_options['scan_archives']:
            cmd_args.append('--scan-archive')
        else:
            cmd_args.append('--scan-archive=no')

        # Add performance options
        if max_file_size > 0:
            cmd_args.extend(['--max-filesize', str(max_file_size * 1024 * 1024)])  # Convert MB to bytes
        if max_scan_time > 0:
            cmd_args.extend(['--max-scantime', str(max_scan_time)])

        # Add file patterns if specified
        exclude_patterns = self.exclude_patterns.text().strip()
        if exclude_patterns and exclude_patterns != '*.log,*.tmp,*.cache':
            for pattern in exclude_patterns.split(','):
                pattern = pattern.strip()
                if pattern:
                    cmd_args.extend(['--exclude', pattern])

        include_patterns = self.include_patterns.text().strip()
        if include_patterns and include_patterns != '*':
            for pattern in include_patterns.split(','):
                pattern = pattern.strip()
                if pattern:
                    cmd_args.extend(['--include', pattern])

        # Add target
        cmd_args.append(target)

        # Start the scan process
        try:
            self.scan_process = QProcess()
            self.scan_process.readyReadStandardOutput.connect(self._handle_external_scan_output)
            self.scan_process.readyReadStandardError.connect(self._handle_external_scan_error)
            self.scan_process.finished.connect(self._handle_external_scan_finished)

            # Start the process
            logger.info(f"Starting external scan with command: {clamscan_path} {' '.join(cmd_args)}")
            self.scan_process.start(clamscan_path, cmd_args)

            if not self.scan_process.waitForStarted(5000):  # 5 second timeout
                raise Exception("Failed to start clamscan process")

        except Exception as e:
            logger.error(f"Error starting external scan: {e}")
            QMessageBox.critical(self, self.tr("External Scan Error"),
                               self.tr(f"Failed to start external scan: {str(e)}"))
            self.scan_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def _handle_external_scan_output(self):
        """Handle output from external scan process."""
        if self.scan_process:
            data = self.scan_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            if data:
                self.output.append(data.strip())

                # Update progress for each scanned file (basic progress indication)
                if 'Scanned file:' in data:
                    current = self.progress.value()
                    if current < 99:
                        self.progress.setValue(min(99, current + 1))

    def _handle_external_scan_error(self):
        """Handle error output from external scan process."""
        if self.scan_process:
            data = self.scan_process.readAllStandardError().data().decode('utf-8', errors='ignore')
            if data:
                self.output.append(f"ERROR: {data.strip()}")

    def _handle_external_scan_finished(self, exit_code, exit_status):
        """Handle external scan completion."""
        # Update UI
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_report_btn.setEnabled(True)
        self.progress.setValue(100)

        # Process results
        if exit_code == 0:
            self.status_bar.showMessage(self.tr("External scan completed successfully"))
            QMessageBox.information(self, self.tr("Scan Complete"),
                                   self.tr("The external scan completed successfully. No threats were found."))
        elif exit_code == 1:
            # Count threats from output (simplified)
            output_text = self.output.toPlainText()
            threat_count = output_text.count('FOUND') + output_text.count('infected')
            self.status_bar.showMessage(self.tr(f"External scan completed - {threat_count} threats found!"))
            QMessageBox.warning(self, self.tr("Threats Detected"),
                               self.tr(f"The external scan completed and found {threat_count} potential threats. Check the scan results for details."))
        else:
            self.status_bar.showMessage(self.tr("External scan failed with errors"))
            QMessageBox.critical(self, self.tr("External Scan Failed"),
                               self.tr("The external scan failed to complete. Please check if ClamAV is properly installed and configured."))

    def on_file_scanned(self, file_path, result):
        """Handle individual file scan results."""
        self.current_scan_results.append(result)

        # Update scan report generator if available
        if hasattr(self, 'scan_report_generator'):
            # Convert ScanFileResult to expected format for report generator
            scan_result = type('ScanResult', (), {
                'file_path': result.file_path,
                'status': result.result.value if hasattr(result.result, 'value') else str(result.result),
                'threat_name': result.threat_name,
                'timestamp': datetime.now()
            })()
            self.scan_report_generator.scan_results.append(scan_result)

    def scan_finished(self, success, message, files_scanned, threats_found):
        """Handle scan completion with enhanced reporting."""
        # Update UI
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_report_btn.setEnabled(True)

        # Update progress to 100%
        if hasattr(self, 'progress'):
            self.progress.setValue(100)

        # Process scan results for auto-quarantine if enabled
        if hasattr(self, 'enable_quarantine') and self.enable_quarantine.isChecked():
            self._auto_quarantine_infected_files()

        # Show appropriate message based on results
        if success:
            if threats_found > 0:
                self.status_bar.showMessage(self.tr(f"Scan completed - {threats_found} threats found!"))
                QMessageBox.warning(
                    self, self.tr("Threats Detected"),
                    self.tr(f"The scan completed and found {threats_found} potential threats.\n\n"
                           "Check the scan results for details and use 'View Quarantine' to manage infected files.")
                )
            else:
                self.status_bar.showMessage(self.tr("Scan completed successfully"))
                QMessageBox.information(
                    self, self.tr("Scan Complete"),
                    self.tr("The scan completed successfully. No threats were found.")
                )
        else:
            self.status_bar.showMessage(self.tr("Scan failed"))
            QMessageBox.critical(
                self, self.tr("Scan Failed"),
                self.tr(f"The scan failed to complete: {message}")
            )
    
    def stop_scan(self):
        """Stop the current scan."""
        # Stop the integrated scan if running
        if hasattr(self, 'clamav_manager') and self.clamav_manager:
            self.clamav_manager.stop_scan()

        # Stop external scan if running
        if hasattr(self, 'scan_process') and self.scan_process:
            if self.scan_process.state() == QProcess.Running:
                self.scan_process.terminate()
                if not self.scan_process.waitForFinished(3000):  # 3 second timeout
                    self.scan_process.kill()  # Force kill if terminate doesn't work

        # Update UI immediately to show cancellation is in progress
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_bar.showMessage(self.tr("Cancelling scan..."))
    
    def update_scan_output(self, text):
        """Update the scan output with new text."""
        self.output.append(text)
        self.output.verticalScrollBar().setValue(
            self.output.verticalScrollBar().maximum()
        )

        # The integrated scanner doesn't use "Scanned file:" format like subprocess
        # Progress is handled by the update_progress signal instead
    
    def update_progress(self, value):
        """Update the progress bar with the current value.

        Args:
            value (int): Progress value from 0 to 100
        """
        if not hasattr(self, 'progress') or not self.progress:
            return

        try:
            # Ensure the value is within valid range
            value = max(0, min(100, int(value)))

            # Update progress bar - for integrated scanner, we use determinate progress
            if hasattr(self, 'progress') and self.progress:
                self.progress.setRange(0, 100)  # Determinate mode for integrated scanner
                self.progress.setValue(value)

                # Force UI update for responsiveness
                QtWidgets.QApplication.processEvents()

        except Exception as e:
            logger.error(f"Error updating progress bar: {e}")
    
    def update_scan_stats(self, status, files_scanned, threats_found):
        """Update scan statistics display."""
        if hasattr(self, 'scan_stats_label'):
            self.scan_stats_label.setText(f"{status} | Files: {files_scanned} | Threats: {threats_found}")
    
    def scan_cancelled(self):
        """Handle scan cancellation."""
        self.status_bar.showMessage(self.tr("Scan cancelled"))
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        QMessageBox.information(self, self.tr("Scan Cancelled"),
                               self.tr("The scan has been cancelled by the user."))
    
    def scan_finished(self, exit_code, _):
        """Handle scan completion.
        
        Args:
            exit_code (int): Exit code of the scan process
            _: Unused parameter (kept for compatibility with signal)
        """
        # Update UI
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_report_btn.setEnabled(True)
        
        # Update progress to 100% when done
        if hasattr(self, 'progress'):
            self.progress.setValue(100)
        
        # Process scan results and generate report
        if hasattr(self, 'scan_report_generator'):
            current_output = self.output.toPlainText()
            self.scan_report_generator.process_scan_output(current_output)
            
            # Auto-quarantine infected files if enabled
            if self.enable_quarantine.isChecked():
                self._auto_quarantine_infected_files()
        
        # Show appropriate message based on exit code
        if exit_code == 0:
            self.status_bar.showMessage(self.tr("Scan completed successfully"))
            QMessageBox.information(self, self.tr("Scan Complete"), 
                                 self.tr("The scan completed successfully. No threats were found."))
        elif exit_code == 1:
            infected_count = len([r for r in self.scan_report_generator.scan_results if r.status == 'infected'])
            self.status_bar.showMessage(self.tr(f"Scan completed - {infected_count} threats found!"))
            QMessageBox.warning(self, self.tr("Threats Detected"), 
                             self.tr(f"The scan completed and found {infected_count} potential threats. Check the scan results for details."))
        else:
            self.status_bar.showMessage(self.tr("Scan failed with errors"))
            QMessageBox.critical(self, self.tr("Scan Failed"), 
                              self.tr("The scan failed to complete. Please check if ClamAV is properly installed and configured."))
    
    def update_update_output(self, text):
        """Update the update output text area with new text.
        
        Args:
            text (str): The text to append to the update output
        """
        if hasattr(self, 'update_output') and self.update_output is not None:
            self.update_output.append(text)
            
    def update_database(self):
        """Update the ClamAV virus database using enhanced updater with error recovery."""
        try:
            # Disconnect any existing connections to avoid duplicates
            if hasattr(self, 'virus_db_updater') and hasattr(self.virus_db_updater, 'signals'):
                try:
                    self.virus_db_updater.signals.disconnect_all()
                except:
                    pass

            # Use error recovery for database updates
            try:
                # Use enhanced update thread with error recovery
                self.update_thread = EnhancedUpdateThread(self.virus_db_updater)
                self.update_thread.update_output.connect(self.update_update_output)
                self.update_thread.update_progress.connect(self.update_progress)
                self.update_thread.finished.connect(self.update_finished)

                # Clear and update UI if we have an update output widget
                if hasattr(self, 'update_output'):
                    self.update_output.clear()

                # Get freshclam path from settings if available
                freshclam_path = None
                if hasattr(self, 'freshclam_path') and self.freshclam_path.text().strip():
                    freshclam_path = self.freshclam_path.text().strip()

                if freshclam_path:
                    self.virus_db_updater = EnhancedVirusDBUpdater(freshclam_path)

                # Start the enhanced update
                self.update_thread.start()

            except Exception as thread_error:
                logger.error(f"Error creating update thread: {thread_error}")
                QMessageBox.critical(self, self.tr("Update Error"),
                                   self.tr(f"Failed to create update thread: {str(thread_error)}"))

        except Exception as e:
            logger.error(f"Error starting database update: {e}")
            QMessageBox.critical(self, self.tr("Update Error"),
                               self.tr(f"Failed to start database update: {str(e)}\n\nPlease check that ClamAV is installed and configured correctly."))
    
    def update_progress(self, value):
        """Update the progress bar with the current value."""
        if hasattr(self, 'progress') and self.progress is not None:
            try:
                # Ensure the value is within valid range
                value = max(0, min(100, int(value)))
                self.progress.setValue(value)
                # Force UI update
                QtWidgets.QApplication.processEvents()
            except Exception as e:
                logger.error(f"Error updating progress bar: {e}")
    
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
    
    def update_finished(self, success, message):
        """Handle update completion."""
        try:
            if success:
                self.status_bar.showMessage(self.tr("Database updated successfully"))
                if hasattr(self, 'progress'):
                    self.progress.setValue(100)

                # Show success message with details
                QMessageBox.information(self, self.tr("Success"),
                                       self.tr(f"Virus database updated successfully.\n\n{message}"))

                # Clean up old backups
                try:
                    if hasattr(self, 'virus_db_updater') and self.virus_db_updater:
                        self.virus_db_updater.cleanup_old_backups(7)  # Keep 7 days of backups
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup old backups: {cleanup_error}")
            else:
                self.status_bar.showMessage(self.tr("Database update failed"))

                # Provide more specific error information
                error_details = message
                if "timeout" in message.lower():
                    error_details += "\n\nThe update timed out. This might be due to network issues or a slow connection."
                elif "not found" in message.lower():
                    error_details += "\n\nClamAV or freshclam might not be installed or not in the system PATH."
                elif "permission" in message.lower() or "access" in message.lower():
                    error_details += "\n\nThere might be permission issues accessing the database directory."

                QMessageBox.warning(self, self.tr("Database Update Failed"),
                                   self.tr(f"Virus database update failed.\n\nError details: {error_details}\n\nPlease check the logs for more information."))

        except Exception as e:
            logger.error(f"Error in update_finished handler: {e}")
            QMessageBox.critical(self, self.tr("Update Error"),
                               self.tr(f"An error occurred while processing the update result: {str(e)}"))
    
    def save_settings(self):
        """Save the application settings."""
        settings = {
            'clamd_path': self.clamd_path.text(),
            'freshclam_path': self.freshclam_path.text(),
            'clamscan_path': self.clamscan_path.text(),
            'scan_archives': self.scan_archives.isChecked(),
            'scan_heuristics': self.scan_heuristics.isChecked(),
            'scan_pua': self.scan_pua.isChecked(),
            'auto_quarantine': self.enable_quarantine.isChecked(),
            'max_file_size': self.max_file_size.text(),
            'max_scan_time': self.max_scan_time.text(),
            'exclude_patterns': self.exclude_patterns.text(),
            'include_patterns': self.include_patterns.text(),
            'enable_smart_scanning': self.enable_smart_scanning.isChecked() if hasattr(self.enable_smart_scanning, 'isChecked') else self.enable_smart_scanning,
            'scanner_type': self.scanner_type_combo.currentData() if hasattr(self, 'scanner_type_combo') else 'integrated'
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
        file_name, _ = QFileDialog.getSaveFileName(self, self.tr("Save Config File"), "", "Config Files (*.conf);;All Files (*)")
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    f.write(self.config_editor.toPlainText())
                QMessageBox.information(self, self.tr("Success"), self.tr("Config file saved successfully"))
            except Exception as e:
                QMessageBox.critical(self, self.tr("Error"), self.tr(f"Failed to save config file: {str(e)}"))
    
    def apply_settings(self):
        """Apply the current settings to the UI."""
        if not self.current_settings:
            return
        
        self.clamd_path.setText(self.current_settings.get('clamd_path', ''))
        self.freshclam_path.setText(self.current_settings.get('freshclam_path', ''))
        self.clamscan_path.setText(self.current_settings.get('clamscan_path', ''))
        
        # Apply scan settings
        scan_settings = self.current_settings
        if 'scan_archives' in scan_settings:
            self.scan_archives.setChecked(scan_settings['scan_archives'])
        if 'scan_heuristics' in scan_settings:
            self.scan_heuristics.setChecked(scan_settings['scan_heuristics'])
        if 'scan_pua' in scan_settings:
            self.scan_pua.setChecked(scan_settings['scan_pua'])
        if 'auto_quarantine' in scan_settings:
            self.enable_quarantine.setChecked(scan_settings.get('auto_quarantine', True))
        if 'max_file_size' in scan_settings:
            self.max_file_size.setText(str(scan_settings['max_file_size']))
        if 'max_scan_time' in scan_settings:
            self.max_scan_time.setText(str(scan_settings['max_scan_time']))
        if 'exclude_patterns' in scan_settings:
            self.exclude_patterns.setText(scan_settings['exclude_patterns'])
        if 'include_patterns' in scan_settings:
            self.include_patterns.setText(scan_settings['include_patterns'])
        if 'scanner_type' in scan_settings:
            if not hasattr(self, 'scanner_type_combo') or self.scanner_type_combo is None:
                # Scanner type combo doesn't exist yet, skip for now
                pass
            else:
                # Find the index for the scanner type and set it
                scanner_type = scan_settings.get('scanner_type', 'integrated')
                for i in range(self.scanner_type_combo.count()):
                    if self.scanner_type_combo.itemData(i) == scanner_type:
                        self.scanner_type_combo.setCurrentIndex(i)
                        break
        if 'enable_smart_scanning' in scan_settings:
            if hasattr(self, 'enable_smart_scanning'):
                self.enable_smart_scanning.setChecked(scan_settings['enable_smart_scanning'])
        
    def _auto_quarantine_infected_files(self):
        """Automatically quarantine infected files found during scan."""
        if not hasattr(self, 'scan_report_generator'):
            return

        infected_files = [r for r in self.scan_report_generator.scan_results if r.status == 'infected']
        quarantined_count = 0

        for result in infected_files:
            success, message = self.quarantine_manager.quarantine_file(
                result.file_path,
                result.threat_name,
                result.timestamp
            )
            if success:
                quarantined_count += 1
                logger.info(f"Auto-quarantined: {result.file_path}")
            else:
                logger.warning(f"Failed to quarantine {result.file_path}: {message}")

        if quarantined_count > 0:
            self.status_bar.showMessage(self.tr(f"Quarantined {quarantined_count} infected files"))
            QMessageBox.information(
                self, self.tr("Files Quarantined"),
                self.tr(f"Successfully quarantined {quarantined_count} infected files.\n\n"
                       "Use 'View Quarantine' to manage quarantined files.")
            )

    def save_scan_report(self):
        """Save the current scan report to a file."""
        if not hasattr(self, 'scan_report_generator'):
            QMessageBox.warning(self, self.tr("Error"), self.tr("No scan report available"))
            return

        file_name, selected_filter = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Scan Report"),
            "",
            "HTML Report (*.html);;Text Report (*.txt);;All Files (*)"
        )

        if not file_name:
            return

        # Determine format from file extension
        if file_name.lower().endswith('.html'):
            format_type = 'html'
        elif file_name.lower().endswith('.txt'):
            format_type = 'text'
        else:
            # Default to HTML
            format_type = 'html'
            if not file_name.lower().endswith('.html'):
                file_name += '.html'

        success = self.scan_report_generator.save_report(file_name, format_type)

        if success:
            QMessageBox.information(
                self, self.tr("Report Saved"),
                self.tr(f"Scan report saved successfully:\n{file_name}")
            )
        else:
            QMessageBox.critical(
                self, self.tr("Save Failed"),
                self.tr("Failed to save scan report")
            )

    def show_quarantine_dialog(self):
        """Show the quarantine management dialog."""
        # For now, just show simple quarantine info since we don't have a full dialog yet
        self._show_simple_quarantine_info()

    def _show_simple_quarantine_info(self):
        """Show basic quarantine information if dialog is not available."""
        try:
            stats = self.quarantine_manager.get_quarantine_stats()
            quarantined_files = self.quarantine_manager.list_quarantined_files()

            info_text = f"""
Quarantine Information:
=====================

Total quarantined files: {stats.get('total_quarantined', 0)}
Total size: {stats.get('total_size_mb', 0):.2f} MB

Threat types found:
{chr(10).join(f"  • {threat}" for threat in stats.get('threat_types', [])) if stats.get('threat_types') else "  None"}

Recent files:
"""
            for file_info in quarantined_files[:5]:  # Show first 5 files
                filename = file_info.get('original_filename', 'Unknown')
                threat = file_info.get('threat_name', 'Unknown')
                info_text += f"  • {filename} ({threat})\n"

            QMessageBox.information(self, self.tr("Quarantine Status"), info_text.strip())

        except Exception as e:
            QMessageBox.information(
                self, self.tr("Quarantine Status"),
                f"Error loading quarantine information: {str(e)}\n\nThe quarantine system may need to be initialized."
            )

    def add_email_file(self):
        """Add an email file to the scan list."""
        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("Select Email Files"),
            "",
            "Email Files (*.eml *.msg);;All Files (*)"
        )
        
        if not file_names:
            return
        
        for file_name in file_names:
            # Check if file already exists in list
            existing_items = self.email_files_list.findItems(os.path.basename(file_name), Qt.MatchExactly)
            if existing_items:
                continue  # Skip duplicates
            
            # Add to list
            item = QListWidgetItem(os.path.basename(file_name))
            item.setData(Qt.UserRole, file_name)  # Store full path
            self.email_files_list.addItem(item)
    
    def remove_email_file(self):
        """Remove selected email files from the scan list."""
        current_row = self.email_files_list.currentRow()
        if current_row >= 0:
            self.email_files_list.takeItem(current_row)
    
    def clear_email_files(self):
        """Clear all email files from the scan list."""
        self.email_files_list.clear()
    
    def start_email_scan(self):
        """Start scanning the selected email files."""
        email_files = []
        for i in range(self.email_files_list.count()):
            item = self.email_files_list.item(i)
            file_path = item.data(Qt.UserRole)
            if file_path and os.path.exists(file_path):
                email_files.append(file_path)
        
        if not email_files:
            QMessageBox.warning(self, self.tr("No Files"), self.tr("Please add email files to scan"))
            return
        
        # Import and initialize email scanner
        from clamav_gui.utils.email_scanner import EmailScanner, EmailScanThread
        
        clamscan_path = self.clamscan_path.text().strip() or "clamscan"
        email_scanner = EmailScanner(clamscan_path)
        
        # Start scan in thread
        self.email_scan_thread = EmailScanThread(email_scanner, email_files)
        self.email_scan_thread.update_progress.connect(self.update_email_progress)
        self.email_scan_thread.update_output.connect(self.update_email_output)
        self.email_scan_thread.finished.connect(self.email_scan_finished)
        
        # Update UI
        self.start_email_scan_btn.setEnabled(False)
        self.stop_email_scan_btn.setEnabled(True)
        self.save_email_report_btn.setEnabled(False)
        self.email_output.clear()
        self.email_progress.setValue(0)
        
        # Start the thread
        self.email_scan_thread.start()
    
    def stop_email_scan(self):
        """Stop the current email scan."""
        if hasattr(self, 'email_scan_thread') and self.email_scan_thread.isRunning():
            self.email_scan_thread.terminate()
            self.email_scan_thread.wait()
            self.email_scan_finished(False, "Scan stopped by user", [])
    
    def update_email_progress(self, value):
        """Update the email scan progress bar."""
        self.email_progress.setValue(value)
    
    def update_email_output(self, text):
        """Update the email scan output."""
        self.email_output.append(text)
        self.email_output.verticalScrollBar().setValue(
            self.email_output.verticalScrollBar().maximum()
        )
    
    def email_scan_finished(self, success, message, threats):
        """Handle email scan completion."""
        # Update UI
        self.start_email_scan_btn.setEnabled(True)
        self.stop_email_scan_btn.setEnabled(False)
        self.save_email_report_btn.setEnabled(True)
        self.email_progress.setValue(100)
        
        # Show results
        if success:
            self.status_bar.showMessage(self.tr(f"Email scan completed - {len(threats)} threats found"))
            if threats:
                QMessageBox.warning(self, self.tr("Threats Detected"), 
                                   self.tr(f"Email scan completed and found {len(threats)} potential threats."))
            else:
                QMessageBox.information(self, self.tr("Scan Complete"), 
                                       self.tr("Email scan completed successfully. No threats were found."))
        else:
            self.status_bar.showMessage(self.tr("Email scan failed"))
            QMessageBox.critical(self, self.tr("Scan Failed"), 
                               self.tr(f"Email scan failed: {message}"))
    
    def save_email_report(self):
        """Save the email scan report to a file."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Email Scan Report"),
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if not file_name:
            return
        
        if not file_name.lower().endswith('.txt'):
            file_name += '.txt'
        
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write("Email Scan Report\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Files Scanned: {self.email_files_list.count()}\n\n")
                f.write("Scan Output:\n")
                f.write("-" * 20 + "\n")
                f.write(self.email_output.toPlainText())
            
            QMessageBox.information(
                self, self.tr("Report Saved"),
                self.tr(f"Email scan report saved successfully:\n{file_name}")
            )
        except Exception as e:
            QMessageBox.critical(
                self, self.tr("Save Failed"),
                self.tr(f"Failed to save email scan report: {str(e)}")
            )

    def generate_scan_report(self):
        """Generate a detailed scan report for the latest scan."""
        try:
            report = self.advanced_reporting.generate_scan_report(format_type='html')

            # Show report in a dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(self.tr("Scan Report"))
            dialog.resize(800, 600)

            layout = QVBoxLayout(dialog)

            text_edit = QTextEdit()
            text_edit.setHtml(report)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)

            btn_layout = QHBoxLayout()
            export_btn = QPushButton(self.tr("Export Report"))
            export_btn.clicked.connect(lambda: self.export_report_dialog(report))
            btn_layout.addWidget(export_btn)

            close_btn = QPushButton(self.tr("Close"))
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)

            layout.addLayout(btn_layout)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr(f"Failed to generate scan report: {str(e)}"))

    def generate_analytics_report(self):
        """Generate analytics report for scan history."""
        try:
            analytics = self.advanced_reporting.generate_analytics_report(30)  # Last 30 days

            if 'error' in analytics:
                QMessageBox.warning(self, self.tr("No Data"),
                                  self.tr(analytics['error']))
                return

            report = []
            report.append("ClamAV Analytics Report (Last 30 Days)")
            report.append("=" * 50)
            report.append(f"Total Scans: {analytics['total_scans']}")
            report.append(f"Files Scanned: {analytics['total_files_scanned']:,}")
            report.append(f"Threats Found: {analytics['total_threats_found']:,}")
            report.append(f"Average Scan Time: {analytics['average_scan_time']:.1f}s")
            report.append(f"Threat Detection Rate: {analytics['threat_detection_rate']:.2f}%")
            report.append("")

            if analytics['most_common_threats']:
                report.append("Most Common Threats:")
                for threat, count in analytics['most_common_threats'][:10]:
                    report.append(f"  {threat}: {count}")
                report.append("")

            report_text = "\n".join(report)

            # Show report in a dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(self.tr("Analytics Report"))
            dialog.resize(600, 400)

            layout = QVBoxLayout(dialog)

            text_edit = QTextEdit()
            text_edit.setPlainText(report_text)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)

            btn_layout = QHBoxLayout()
            export_btn = QPushButton(self.tr("Export Report"))
            export_btn.clicked.connect(lambda: self.export_analytics_dialog(analytics))
            btn_layout.addWidget(export_btn)

            close_btn = QPushButton(self.tr("Close"))
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)

            layout.addLayout(btn_layout)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr(f"Failed to generate analytics report: {str(e)}"))

    def generate_threat_intelligence_report(self):
        """Generate threat intelligence report."""
        try:
            report = self.advanced_reporting.generate_threat_intelligence_report()

            # Show report in a dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(self.tr("Threat Intelligence Report"))
            dialog.resize(600, 400)

            layout = QVBoxLayout(dialog)

            text_edit = QTextEdit()
            text_edit.setPlainText(report)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)

            btn_layout = QHBoxLayout()
            export_btn = QPushButton(self.tr("Export Report"))
            export_btn.clicked.connect(lambda: self.export_ti_dialog(report))
            btn_layout.addWidget(export_btn)

            close_btn = QPushButton(self.tr("Close"))
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)

            layout.addLayout(btn_layout)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr(f"Failed to generate threat intelligence report: {str(e)}"))

    def export_report_dialog(self, report_content):
        """Show export dialog for scan report."""
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self,
            self.tr("Export Scan Report"),
            "",
            "HTML Files (*.html);;Text Files (*.txt);;All Files (*)"
        )

        if not file_name:
            return

        # Determine format from file extension
        if file_name.lower().endswith('.html'):
            format_type = 'html'
        elif file_name.lower().endswith('.txt'):
            format_type = 'txt'
        else:
            # Default to HTML
            format_type = 'html'
            if not file_name.lower().endswith('.html'):
                file_name += '.html'

        success = self.advanced_reporting.export_report(report_content, file_name, format_type)

        if success:
            QMessageBox.information(self, self.tr("Export Successful"),
                                  self.tr(f"Report exported successfully:\n{file_name}"))
        else:
            QMessageBox.critical(self, self.tr("Export Failed"),
                               self.tr("Failed to export report"))

    def export_analytics_dialog(self, analytics_data):
        """Show export dialog for analytics report."""
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self,
            self.tr("Export Analytics Report"),
            "",
            "JSON Files (*.json);;CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )

        if not file_name:
            return

        # Determine format from file extension
        if file_name.lower().endswith('.json'):
            format_type = 'json'
        elif file_name.lower().endswith('.csv'):
            format_type = 'csv'
        elif file_name.lower().endswith('.txt'):
            format_type = 'txt'
        else:
            format_type = 'json'
            if not file_name.lower().endswith('.json'):
                file_name += '.json'

        if format_type == 'txt':
            # Generate text report from analytics data
            report_lines = []
            report_lines.append("ClamAV Analytics Report (Last 30 Days)")
            report_lines.append("=" * 50)
            report_lines.append(f"Total Scans: {analytics_data['total_scans']}")
            report_lines.append(f"Files Scanned: {analytics_data['total_files_scanned']:,}")
            report_lines.append(f"Threats Found: {analytics_data['total_threats_found']:,}")
            report_lines.append(f"Average Scan Time: {analytics_data['average_scan_time']:.1f}s")
            report_lines.append(f"Threat Detection Rate: {analytics_data['threat_detection_rate']:.2f}%")

            report_content = "\n".join(report_lines)
            success = self.advanced_reporting.export_report(report_content, file_name, 'txt')
        else:
            # For JSON/CSV, use the analytics data directly
            success = self.advanced_reporting.export_report(json.dumps(analytics_data), file_name, format_type)

        if success:
            QMessageBox.information(self, self.tr("Export Successful"),
                                  self.tr(f"Analytics report exported successfully:\n{file_name}"))
        else:
            QMessageBox.critical(self, self.tr("Export Failed"),
                               self.tr("Failed to export analytics report"))

    def export_ti_dialog(self, report_content):
        """Show export dialog for threat intelligence report."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export Threat Intelligence Report"),
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if not file_name:
            return

        if not file_name.lower().endswith('.txt'):
            file_name += '.txt'

        success = self.advanced_reporting.export_report(report_content, file_name, 'txt')

        if success:
            QMessageBox.information(self, self.tr("Export Successful"),
                                  self.tr(f"Threat intelligence report exported successfully:\n{file_name}"))
        else:
            QMessageBox.critical(self, self.tr("Export Failed"),
                               self.tr("Failed to export threat intelligence report"))

    def export_current_report(self):
        """Export the current scan report if available."""
        # Check if we have recent scan data
        if hasattr(self, 'scan_report_generator') and self.scan_report_generator.scan_results:
            # Generate report from current scan results
            report_data = {
                'scan_type': 'manual',
                'target': getattr(self, 'target_input', {}).text() if hasattr(self, 'target_input') else '',
                'total_files': 0,
                'scanned_files': 0,
                'threats_found': 0,
                'threats': [],
                'scan_time_seconds': 0,
                'settings_used': {}
            }

            # Add scan results
            for result in self.scan_report_generator.scan_results:
                report_data['scanned_files'] += 1
                if result.status == 'infected':
                    report_data['threats_found'] += 1
                    report_data['threats'].append({
                        'name': result.threat_name,
                        'file_path': result.file_path
                    })

            # Add to reporting system
            self.advanced_reporting.add_scan_result(report_data)

            # Generate and export report
            report = self.advanced_reporting.generate_scan_report(format_type='html')
            self.export_report_dialog(report)
        else:
            QMessageBox.information(self, self.tr("No Data"),
                                  self.tr("No current scan data available for export"))

    def analyze_file_with_ml(self):
        """Analyze a single file using ML threat detection."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select File for ML Analysis"),
            "",
            "All Files (*)"
        )

        if not file_name:
            return

        try:
            # Perform ML analysis
            analysis_result = self.sandbox_analyzer.analyze_file(file_name)

            if 'error' in analysis_result:
                QMessageBox.critical(self, self.tr("Analysis Error"),
                                   self.tr(f"Failed to analyze file: {analysis_result['error']}"))
                return

            # Display results in a dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(self.tr("ML Analysis Results"))
            dialog.resize(600, 400)

            layout = QVBoxLayout(dialog)

            # Results display
            results_text = QTextEdit()
            results_text.setReadOnly(True)

            result_lines = []
            result_lines.append("Machine Learning Analysis Results")
            result_lines.append("=" * 40)
            result_lines.append(f"File: {analysis_result['file_path']}")
            result_lines.append(f"ML Confidence: {analysis_result['ml_confidence']:.3f}")
            result_lines.append(f"ML Category: {analysis_result['ml_category']}")
            result_lines.append(f"Risk Level: {analysis_result['risk_level'].upper()}")
            result_lines.append(f"File Size: {analysis_result['file_size']:,} bytes")
            result_lines.append(f"Entropy: {analysis_result['entropy']:.2f}")
            result_lines.append(f"Is Executable: {'Yes' if analysis_result['is_executable'] else 'No'}")
            result_lines.append(f"Analysis Time: {analysis_result['analysis_timestamp']}")

            results_text.setPlainText("\n".join(result_lines))
            layout.addWidget(results_text)

            # Action buttons
            btn_layout = QHBoxLayout()

            # Risk level indicator
            risk_color = {'low': 'green', 'medium': 'orange', 'high': 'red'}.get(analysis_result['risk_level'], 'gray')
            risk_label = QLabel(f"Risk Level: <span style='color: {risk_color}; font-weight: bold;'>{analysis_result['risk_level'].upper()}</span>")
            btn_layout.addWidget(risk_label)
            btn_layout.addStretch()

            export_btn = QPushButton(self.tr("Export Results"))
            export_btn.clicked.connect(lambda: self.export_ml_analysis(analysis_result))
            btn_layout.addWidget(export_btn)

            close_btn = QPushButton(self.tr("Close"))
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)

            layout.addLayout(btn_layout)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr(f"Failed to perform ML analysis: {str(e)}"))

    def batch_analyze_files(self):
        """Perform batch ML analysis on multiple files."""
        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("Select Files for Batch ML Analysis"),
            "",
            "All Files (*)"
        )

        if not file_names:
            return

        try:
            # Perform batch analysis
            results = self.sandbox_analyzer.batch_analyze(file_names)

            # Display results in a dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(self.tr("Batch ML Analysis Results"))
            dialog.resize(800, 600)

            layout = QVBoxLayout(dialog)

            # Summary statistics
            summary_text = QTextEdit()
            summary_text.setReadOnly(True)

            total_files = len(results)
            risk_counts = {'high': 0, 'medium': 0, 'low': 0}
            ml_detections = 0

            for result in results:
                if 'error' not in result:
                    risk_counts[result.get('risk_level', 'low')] += 1
                    if result.get('ml_confidence', 0) > 0.5:
                        ml_detections += 1

            summary_lines = []
            summary_lines.append("Batch ML Analysis Summary")
            summary_lines.append("=" * 30)
            summary_lines.append(f"Total Files: {total_files}")
            summary_lines.append(f"ML Detections: {ml_detections}")
            summary_lines.append("")
            summary_lines.append("Risk Distribution:")
            for level, count in risk_counts.items():
                percentage = (count / total_files * 100) if total_files > 0 else 0
                summary_lines.append(f"  {level.upper()}: {count} ({percentage:.1f}%)")

            summary_text.setPlainText("\n".join(summary_lines))
            layout.addWidget(summary_text)

            # Detailed results table
            results_table = QTableWidget()
            results_table.setColumnCount(5)
            results_table.setHorizontalHeaderLabels([
                self.tr("File"), self.tr("Risk Level"), self.tr("ML Confidence"),
                self.tr("Category"), self.tr("File Size")
            ])

            results_table.setRowCount(len(results))

            for i, result in enumerate(results):
                if 'error' in result:
                    results_table.setItem(i, 0, QTableWidgetItem(result['file_path']))
                    results_table.setItem(i, 1, QTableWidgetItem("ERROR"))
                    results_table.setItem(i, 2, QTableWidgetItem(str(result['error'])))
                    results_table.setItem(i, 3, QTableWidgetItem(""))
                    results_table.setItem(i, 4, QTableWidgetItem(""))
                else:
                    results_table.setItem(i, 0, QTableWidgetItem(os.path.basename(result['file_path'])))
                    results_table.setItem(i, 1, QTableWidgetItem(result.get('risk_level', 'unknown').upper()))
                    results_table.setItem(i, 2, QTableWidgetItem(f"{result.get('ml_confidence', 0):.3f}"))
                    results_table.setItem(i, 3, QTableWidgetItem(result.get('ml_category', 'unknown')))
                    results_table.setItem(i, 4, QTableWidgetItem(f"{result.get('file_size', 0):,}"))


            results_table.resizeColumnsToContents()
            layout.addWidget(results_table)

            # Action buttons
            btn_layout = QHBoxLayout()

            export_btn = QPushButton(self.tr("Export Report"))
            export_btn.clicked.connect(lambda: self.export_batch_analysis(results))
            btn_layout.addWidget(export_btn)

            close_btn = QPushButton(self.tr("Close"))
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)

            layout.addLayout(btn_layout)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr(f"Failed to perform batch analysis: {str(e)}"))

    def train_ml_model(self):
        """Train the ML model (placeholder for future implementation)."""
        QMessageBox.information(
            self,
            self.tr("Training Not Available"),
            self.tr("ML model training requires labeled training data and is not yet implemented.\n\n"
                   "This feature would allow training custom ML models on your specific threat data.")
        )

    def show_ml_model_info(self):
        """Show information about the current ML model."""
        model_info = self.ml_detector.get_model_info()

        info_text = "Machine Learning Model Information\n"
        info_text += "=" * 40 + "\n"

        if model_info['status'] == 'not_trained':
            info_text += "Status: No trained model available\n"
            info_text += "The ML threat detection feature requires training data to function.\n"
        else:
            info_text += f"Status: {model_info['status']}\n"
            info_text += f"Model Type: {model_info['model_type']}\n"
            info_text += f"Features: {model_info['feature_count']}\n"
            info_text += f"Classes: {', '.join(model_info['classes'])}\n"

        QMessageBox.information(self, self.tr("ML Model Info"), info_text)

    def export_ml_analysis(self, analysis_result):
        """Export ML analysis results."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export ML Analysis"),
            "",
            "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
        )

        if not file_name:
            return

        # Determine format
        if file_name.lower().endswith('.json'):
            content = json.dumps(analysis_result, indent=2, ensure_ascii=False)
        else:
            # Text format
            lines = []
            lines.append("Machine Learning Analysis Results")
            lines.append("=" * 40)
            for key, value in analysis_result.items():
                if key != 'file_path':  # Skip file path in summary
                    lines.append(f"{key.replace('_', ' ').title()}: {value}")
            content = "\n".join(lines)

            if not file_name.lower().endswith('.txt'):
                file_name += '.txt'

        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(content)

            QMessageBox.information(self, self.tr("Export Successful"),
                                  self.tr(f"ML analysis exported successfully:\n{file_name}"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Export Failed"),
                               self.tr(f"Failed to export ML analysis: {str(e)}"))

    def export_batch_analysis(self, results):
        """Export batch analysis results."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export Batch Analysis"),
            "",
            "Text Files (*.txt);;JSON Files (*.json);;All Files (*)"
        )

        if not file_name:
            return

        # Generate report
        report = self.sandbox_analyzer.generate_ml_report(results)

        # Determine format
        if file_name.lower().endswith('.json'):
            content = json.dumps(results, indent=2, ensure_ascii=False)
        else:
            content = report
            if not file_name.lower().endswith('.txt'):
                file_name += '.txt'

        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(content)

            QMessageBox.information(self, self.tr("Export Successful"),
                                  self.tr(f"Batch analysis exported successfully:\n{file_name}"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Export Failed"),
                               self.tr(f"Failed to export batch analysis: {str(e)}"))

    def sandbox_analyze_file(self):
        """Analyze a file in the sandbox environment."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select File for Sandbox Analysis"),
            "",
            "All Files (*)"
        )

        if not file_name:
            return

        try:
            # Perform sandbox analysis
            analysis_result = self.sandbox_analyzer.analyze_file_behavior(file_name)

            if 'error' in analysis_result:
                QMessageBox.critical(self, self.tr("Analysis Error"),
                                   self.tr(f"Failed to analyze file: {analysis_result['error']}"))
                return

            # Generate report
            report = self.sandbox_analyzer.generate_sandbox_report(analysis_result)

            # Display results in a dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(self.tr("Sandbox Analysis Results"))
            dialog.resize(700, 500)

            layout = QVBoxLayout(dialog)

            # Summary section
            summary_text = QTextEdit()
            summary_text.setReadOnly(True)

            risk_level = analysis_result.get('risk_assessment', {}).get('risk_level', 'unknown')
            risk_color = {'low': 'green', 'medium': 'orange', 'high': 'red'}.get(risk_level, 'gray')

            summary_lines = []
            summary_lines.append("Sandbox Analysis Summary")
            summary_lines.append("=" * 30)
            summary_lines.append(f"Risk Level: <span style='color: {risk_color}; font-weight: bold;'>{risk_level.upper()}</span>")
            summary_lines.append(f"Analysis Duration: {analysis_result.get('analysis_duration', 0):.2f}s")
            summary_lines.append("")

            if risk_level == 'high':
                summary_lines.append("⚠️ HIGH RISK DETECTED")
                summary_lines.append("This file shows suspicious behavior and should be handled with extreme caution.")
            elif risk_level == 'medium':
                summary_lines.append("⚡ MEDIUM RISK DETECTED")
                summary_lines.append("This file shows some suspicious behavior. Monitor system after use.")
            else:
                summary_lines.append("✅ LOW RISK")
                summary_lines.append("This file appears safe for normal use.")

            summary_text.setHtml("\n".join(summary_lines))
            layout.addWidget(summary_text)

            # Detailed report
            report_text = QTextEdit()
            report_text.setPlainText(report)
            report_text.setReadOnly(True)
            layout.addWidget(report_text)

            # Action buttons
            btn_layout = QHBoxLayout()

            export_btn = QPushButton(self.tr("Export Report"))
            export_btn.clicked.connect(lambda: self.export_sandbox_report(analysis_result))
            btn_layout.addWidget(export_btn)

            close_btn = QPushButton(self.tr("Close"))
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)

            layout.addLayout(btn_layout)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr(f"Failed to perform sandbox analysis: {str(e)}"))

    def batch_sandbox_analysis(self):
        """Perform batch sandbox analysis on multiple files."""
        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("Select Files for Batch Sandbox Analysis"),
            "",
            "All Files (*)"
        )

        if not file_names:
            return

        try:
            # Perform batch analysis
            results = self.sandbox_analyzer.batch_sandbox_analysis(file_names)

            # Display results in a dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(self.tr("Batch Sandbox Analysis Results"))
            dialog.resize(900, 600)

            layout = QVBoxLayout(dialog)

            # Summary statistics
            summary_text = QTextEdit()
            summary_text.setReadOnly(True)

            total_files = len(results)
            risk_counts = {'high': 0, 'medium': 0, 'low': 0}
            errors = 0

            for result in results:
                if 'error' in result:
                    errors += 1
                else:
                    risk_level = result.get('risk_assessment', {}).get('risk_level', 'low')
                    risk_counts[risk_level] += 1

            summary_lines = []
            summary_lines.append("Batch Sandbox Analysis Summary")
            summary_lines.append("=" * 35)
            summary_lines.append(f"Total Files: {total_files}")
            summary_lines.append(f"Successful Analyses: {total_files - errors}")
            summary_lines.append(f"Errors: {errors}")
            summary_lines.append("")
            summary_lines.append("Risk Distribution:")
            for level, count in risk_counts.items():
                percentage = (count / (total_files - errors) * 100) if (total_files - errors) > 0 else 0
                summary_lines.append(f"  {level.upper()}: {count} ({percentage:.1f}%)")

            summary_text.setPlainText("\n".join(summary_lines))
            layout.addWidget(summary_text)

            # Results table
            results_table = QTableWidget()
            results_table.setColumnCount(3)
            results_table.setHorizontalHeaderLabels([
                self.tr("File"), self.tr("Risk Level"), self.tr("Status")
            ])

            results_table.setRowCount(len(results))

            for i, result in enumerate(results):
                file_name = os.path.basename(result.get('file_info', {}).get('path', 'Unknown')) if 'file_info' in result else 'Unknown'

                if 'error' in result:
                    results_table.setItem(i, 0, QTableWidgetItem(file_name))
                    results_table.setItem(i, 1, QTableWidgetItem("ERROR"))
                    results_table.setItem(i, 2, QTableWidgetItem(result['error']))
                else:
                    risk_level = result.get('risk_assessment', {}).get('risk_level', 'unknown')
                    results_table.setItem(i, 0, QTableWidgetItem(file_name))
                    results_table.setItem(i, 1, QTableWidgetItem(risk_level.upper()))
                    results_table.setItem(i, 2, QTableWidgetItem("Analyzed"))

            results_table.resizeColumnsToContents()
            layout.addWidget(results_table)

            # Action buttons
            btn_layout = QHBoxLayout()

            export_btn = QPushButton(self.tr("Export Report"))
            export_btn.clicked.connect(lambda: self.export_batch_sandbox_report(results))
            btn_layout.addWidget(export_btn)

            close_btn = QPushButton(self.tr("Close"))
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)

            layout.addLayout(btn_layout)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr(f"Failed to perform batch sandbox analysis: {str(e)}"))

    def show_sandbox_capabilities(self):
        """Show information about sandbox analysis capabilities."""
        capabilities = self.sandbox_analyzer.get_sandbox_capabilities()

        info_text = "Sandbox Analysis Capabilities\n"
        info_text += "=" * 35 + "\n"
        info_text += f"Platform Support: {', '.join(capabilities.get('supported_platforms', []))}\n"
        info_text += f"Analysis Timeout: {capabilities.get('analysis_timeout', 0)} seconds\n"
        info_text += f"Memory Limit: {capabilities.get('max_memory_limit', 0) / (1024*1024):.0f} MB\n"
        info_text += "\nMonitoring Features:\n"

        for feature in capabilities.get('monitoring_features', []):
            info_text += f"  • {feature.replace('_', ' ').title()}\n"

        info_text += "\nSupported File Types:\n"
        if capabilities.get('supports_scripts'):
            info_text += "  • Batch files (.bat, .cmd)\n"
        if capabilities.get('supports_windows_executables'):
            info_text += "  • Windows executables (.exe, .dll)\n"

        QMessageBox.information(self, self.tr("Sandbox Capabilities"), info_text)

    def export_sandbox_report(self, analysis_result):
        """Export sandbox analysis results."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export Sandbox Analysis"),
            "",
            "Text Files (*.txt);;JSON Files (*.json);;All Files (*)"
        )

        if not file_name:
            return

        # Generate report
        report = self.sandbox_analyzer.generate_sandbox_report(analysis_result)

        # Determine format
        if file_name.lower().endswith('.json'):
            content = json.dumps(analysis_result, indent=2, ensure_ascii=False)
        else:
            content = report
            if not file_name.lower().endswith('.txt'):
                file_name += '.txt'

        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(content)

            QMessageBox.information(self, self.tr("Export Successful"),
                                  self.tr(f"Sandbox analysis exported successfully:\n{file_name}"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Export Failed"),
                               self.tr(f"Failed to export sandbox analysis: {str(e)}"))

    def export_batch_sandbox_report(self, results):
        """Export batch sandbox analysis results."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export Batch Sandbox Analysis"),
            "",
            "Text Files (*.txt);;JSON Files (*.json);;All Files (*)"
        )

        if not file_name:
            return

        # Generate combined report
        report_lines = []
        report_lines.append("Batch Sandbox Analysis Report")
        report_lines.append("=" * 40)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Files Analyzed: {len(results)}")
        report_lines.append("")

        for i, result in enumerate(results):
            if 'error' in result:
                report_lines.append(f"File {i+1}: ERROR - {result['error']}")
            else:
                risk_level = result.get('risk_assessment', {}).get('risk_level', 'unknown')
                file_name = os.path.basename(result.get('file_info', {}).get('path', 'Unknown'))
                report_lines.append(f"File {i+1}: {file_name} - Risk: {risk_level.upper()}")

        report = "\n".join(report_lines)

        # Determine format
        if file_name.lower().endswith('.json'):
            content = json.dumps(results, indent=2, ensure_ascii=False)
        else:
            content = report
            if not file_name.lower().endswith('.txt'):
                file_name += '.txt'

        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(content)

            QMessageBox.information(self, self.tr("Export Successful"),
                                  self.tr(f"Batch sandbox analysis exported successfully:\n{file_name}"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Export Failed"),
                               self.tr(f"Failed to export batch sandbox analysis: {str(e)}"))

    """Thread for running ClamAV scans with enhanced async support."""
    update_output = Signal(str)
    update_progress = Signal(int)  # Signal for progress updates (0-100)
    update_stats = Signal(str, int, int)  # Signal for scan statistics (files_scanned, threats_found)
    finished = Signal(int, int)
    cancelled = Signal()

    def __init__(self, command, enable_smart_scanning=False):
        super().__init__()
        self.command = command
        self.enable_smart_scanning = enable_smart_scanning
        self.process = None
        self.cancelled_flag = False
        self.hash_db = None

        # Initialize hash database for smart scanning if enabled
        if enable_smart_scanning:
            try:
                from clamav_gui.utils.hash_database import HashDatabase
                self.hash_db = HashDatabase()
            except ImportError:
                logger.warning("HashDatabase not available for smart scanning")

    def cancel(self):
        """Cancel the scan operation."""
        self.cancelled_flag = True
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()
            # Give it a moment to terminate gracefully, then kill if needed
            if not self.process.waitForFinished(3000):  # 3 seconds
                self.process.kill()

    def run(self):
        """Run the scan command with enhanced async support."""
        try:
            if self.cancelled_flag:
                self.cancelled.emit()
                return

            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.handle_output)
            self.process.readyReadStandardError.connect(self.handle_error)

            # Enhanced finished signal handling
            self.process.finished.connect(self.on_finished)

            # Start the process
            self.process.start(self.command[0], self.command[1:])

            # Track progress with enhanced statistics
            total_files = 0
            processed_files = 0
            threats_found = 0
            last_progress = 0
            start_time = time.time()

            # First, count total files if possible (with smart scanning support)
            if 'clamscan' in self.command[0].lower() and len(self.command) > 1:
                try:
                    target = self.command[-1]
                    if os.path.isdir(target):
                        # Use smart scanning to filter files if enabled
                        if self.enable_smart_scanning and self.hash_db:
                            # Count only files that need scanning
                            all_files = list(Path(target).rglob('*'))
                            files_to_scan = []
                            for file_path in all_files:
                                if file_path.is_file():
                                    file_hash = self.hash_db.get_file_hash(str(file_path))
                                    if not self.hash_db.is_known_safe(file_hash):
                                        files_to_scan.append(file_path)
                                    else:
                                        # Mark known safe files in output
                                        self.update_output.emit(f"Skipped (known safe): {file_path.name}")

                            total_files = len(files_to_scan)
                            if total_files > 0:
                                self.update_output.emit(f"Found {len(all_files)} files, {total_files} need scanning (smart scan enabled)")
                            else:
                                self.update_output.emit(f"All {len(all_files)} files are known safe - no scanning needed")
                                self.update_progress.emit(100)
                                self.finished.emit(0, 0)  # Clean exit
                                return
                        else:
                            total_files = sum(1 for _ in Path(target).rglob('*') if _.is_file())
                            self.update_output.emit(f"Found {total_files} files to scan")
                    elif os.path.isfile(target):
                        total_files = 1
                except Exception as e:
                    self.update_output.emit(f"Could not count files: {str(e)}")

            # Emit initial progress
            self.update_progress.emit(0)
            self.update_stats.emit("Ready", 0, 0)

            # Buffer for partial lines
            buffer = ""
            last_update = time.time()

            while not self.process.waitForFinished(100):  # Check every 100ms
                if self.cancelled_flag:
                    self.update_output.emit("Scan cancelled by user")
                    self.cancelled.emit()
                    return

                # Read all available output
                output = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
                if not output:
                    continue

                # Add to buffer and split by lines
                buffer += output
                lines = buffer.split('\n')
                buffer = lines.pop()  # Keep the last incomplete line in buffer

                # Process complete lines
                for line in lines:
                    if not line.strip():
                        continue

                    self.update_output.emit(line)

                    # Update progress for each scanned file (enhanced)
                    if 'Scanned file:' in line:
                        processed_files += 1

                        # Update statistics
                        if threats_found == 0:  # Only update if no threats found yet
                            self.update_stats.emit(f"Scanning... ({processed_files}/{total_files})", processed_files, threats_found)

                        # More responsive progress updates
                        current_time = time.time()
                        if current_time - last_update >= 0.05:  # Update up to 20 times per second
                            if total_files > 0:
                                progress = min(99, int((processed_files / total_files) * 100))
                            else:
                                progress = min(99, processed_files % 100)

                            if progress != last_progress:
                                self.update_progress.emit(progress)
                                last_progress = progress
                                # Update UI more frequently for better responsiveness
                                QtWidgets.QApplication.processEvents()

                            last_update = current_time

                    # Track threats found
                    elif 'FOUND' in line or 'infected' in line.lower():
                        threats_found += 1
                        self.update_stats.emit(f"Scanning... ({processed_files}/{total_files})", processed_files, threats_found)

                        # Extract file path and threat name for hash database update
                        if self.enable_smart_scanning and self.hash_db:
                            # Try to extract file path from the line
                            # This is a simplified approach - in practice, we'd need more sophisticated parsing
                            pass

                    # Try to get total files from summary if not already known
                    elif total_files == 0 and ' files, ' in line and 'infested files: ' in line:
                        try:
                            parts = line.split(' files, ')
                            if len(parts) > 1:
                                total_files = int(parts[0].split()[-1])
                                self.update_output.emit(f"Found {total_files} files to scan in total")
                        except (ValueError, IndexError):
                            pass

            # Final statistics update
            self.update_stats.emit("Complete", processed_files, threats_found)

        except Exception as e:
            if not self.cancelled_flag:
                self.update_output.emit(f"Scan error: {str(e)}")
                self.finished.emit(1, 1)
            else:
                self.cancelled.emit()

    def handle_output(self):
        """Handle standard output from the process."""
        if self.process and not self.cancelled_flag:
            data = self.process.readAllStandardOutput().data().decode()
            self.update_output.emit(data)

    def handle_error(self):
        """Handle error output from the process."""
        if self.process and not self.cancelled_flag:
            data = self.process.readAllStandardError().data().decode()
            self.update_output.emit(data)

    def on_finished(self, exit_code, exit_status):
        """Handle process completion."""
        if not self.cancelled_flag:
            self.finished.emit(exit_code, exit_status)
        else:
            self.cancelled.emit()


class UpdateThread(QThread):
    """Thread for updating the ClamAV database."""
    update_output = Signal(str)
    finished = Signal(int, int)
    
    def __init__(self, command):
        super().__init__()
        self.command = command
        self.process = None
    
    def run(self):
        """Run the update command."""
        try:
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.handle_output)
            self.process.readyReadStandardError.connect(self.handle_error)
            self.process.finished.connect(self.on_finished)
            
            # Start the process
            self.process.start(self.command[0], self.command[1:])
            self.process.waitForFinished(-1)
            
        except Exception as e:
            self.update_output.emit(str(e))
            self.finished.emit(1, 1)
    
    def handle_output(self):
        """Handle standard output from the process."""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode()
            self.update_output.emit(data)
    
    def handle_error(self):
        """Handle error output from the process."""
        if self.process:
            data = self.process.readAllStandardError().data().decode()
            self.update_output.emit(data)
    
    def on_finished(self, exit_code, exit_status):
        """Handle process completion."""
        self.finished.emit(exit_code, exit_status)
    
    def show_network_scanning(self):
        """Show network scanning interface."""
        try:
            # Switch to scan tab and set network scanning mode
            if hasattr(self, 'tabs'):
                for i in range(self.tabs.count()):
                    if self.tabs.tabText(i) == self.tr("Scan"):
                        self.tabs.setCurrentIndex(i)
                        break

            # Set target to network path
            if hasattr(self, 'target_input'):
                network_dialog = NetworkPathDialog(self)
                if network_dialog.exec() == QDialog.Accepted:
                    selected_path = network_dialog.get_selected_path()
                    if selected_path:
                        self.target_input.setText(selected_path)
                        self.add_activity_entry(f"Network scanning initiated for: {selected_path}")

        except Exception as e:
            logger.error(f"Error opening network scanning: {e}")
            QMessageBox.critical(
                self, self.tr("Network Scanning Error"),
                self.tr(f"Failed to open network scanning interface:\n\n{str(e)}")
            )

    def show_batch_analysis(self):
        """Show batch analysis interface."""
        try:
            # Switch to scan tab for batch file selection
            if hasattr(self, 'tabs'):
                for i in range(self.tabs.count()):
                    if self.tabs.tabText(i) == self.tr("Scan"):
                        self.tabs.setCurrentIndex(i)
                        break

            # Open file dialog for multiple file selection
            file_names, _ = QFileDialog.getOpenFileNames(
                self,
                self.tr("Select Files for Batch Analysis"),
                "",
                "All Files (*);;Executable Files (*.exe *.dll);;Documents (*.pdf *.doc *.docx)"
            )

            if file_names:
                # Set first file as target and show batch mode
                if hasattr(self, 'target_input'):
                    self.target_input.setText(f"{len(file_names)} files selected for batch analysis")

                # Store batch files for processing
                self.batch_files = file_names
                self.add_activity_entry(f"Batch analysis initiated for {len(file_names)} files")

                # Enable batch mode checkbox if it exists
                if hasattr(self, 'batch_mode_checkbox'):
                    self.batch_mode_checkbox.setChecked(True)

        except Exception as e:
            logger.error(f"Error opening batch analysis: {e}")
            QMessageBox.critical(
                self, self.tr("Batch Analysis Error"),
                self.tr(f"Failed to open batch analysis interface:\n\n{str(e)}")
            )

    def show_ml_detection(self):
        """Show ML threat detection interface."""
        try:
            # Check if ML detector is available
            if not hasattr(self, 'ml_detector') or not self.ml_detector:
                QMessageBox.information(
                    self, self.tr("ML Detection Not Available"),
                    self.tr("Machine Learning threat detection is not available.\n\n"
                           "This feature requires additional ML libraries and trained models.")
                )
                return

            # Switch to ML analysis tab or show ML dialog
            ml_dialog = MLDetectionDialog(self.ml_detector, self)
            ml_dialog.exec()

        except Exception as e:
            logger.error(f"Error opening ML detection: {e}")
            QMessageBox.critical(
                self, self.tr("ML Detection Error"),
                self.tr(f"Failed to open ML detection interface:\n\n{str(e)}")
            )

    def show_smart_scanning(self):
        """Show smart scanning interface and configuration."""
        try:
            # Check if hash database is available
            if not hasattr(self, 'hash_database') or not self.hash_database:
                QMessageBox.information(
                    self, self.tr("Smart Scanning Not Available"),
                    self.tr("Smart scanning requires a hash database.\n\n"
                           "Please ensure the hash database is properly configured.")
                )
                return

            # Show smart scanning configuration dialog
            smart_dialog = SmartScanningDialog(self.hash_database, self)
            smart_dialog.exec()

        except Exception as e:
            logger.error(f"Error opening smart scanning: {e}")
            QMessageBox.critical(
                self, self.tr("Smart Scanning Error"),
                self.tr(f"Failed to open smart scanning interface:\n\n{str(e)}")
            )
