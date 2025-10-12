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
from clamav_gui.ui.about import AboutDialog
from clamav_gui.ui.sponsor import SponsorDialog
from clamav_gui.utils.virus_db import VirusDBUpdater

# Import language manager
from clamav_gui.lang.lang_manager import SimpleLanguageManager

# Import ClamAV validator
from clamav_gui.utils.clamav_validator import ClamAVValidator

# Import scan report generator
from clamav_gui.utils.scan_report import ScanReportGenerator

# Import quarantine manager
from clamav_gui.utils.quarantine_manager import QuarantineManager

# Import enhanced database updater
from clamav_gui.utils.enhanced_db_updater import EnhancedVirusDBUpdater, EnhancedUpdateThread

# Import hash database for smart scanning
from clamav_gui.utils.hash_database import HashDatabase

# Import error recovery system
from clamav_gui.utils.error_recovery import ErrorRecoveryManager, ErrorType, NetworkErrorRecovery

# Setup logger
logger = logging.getLogger(__name__)

from .ui.UI import ClamAVMainWindow

class ClamAVGUI(ClamAVMainWindow):
    """Main window for the ClamAV GUI application."""
    
    def __init__(self, lang_manager=None, parent=None):
        """Initialize the main window.
        
        Args:
            lang_manager: Instance of SimpleLanguageManager for translations
            parent: Parent widget
        """
        super().__init__(parent)
        self.settings = AppSettings()
        self.process = None
        self.scan_thread = None
        self.virus_db_updater = EnhancedVirusDBUpdater()
        self.hash_database = HashDatabase()
        self.clamav_validator = ClamAVValidator()
        self.scan_report_generator = ScanReportGenerator()
        self.quarantine_manager = QuarantineManager()
        self.error_recovery = ErrorRecoveryManager()
        self.network_recovery = NetworkErrorRecovery()
        
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
        
        # Initialize UI
        self.init_ui()
        
        # Load settings
        self.current_settings = self.settings.load_settings()
        self.apply_settings()
        
        # Apply language
        self.retranslate_ui()
    
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
        self.email_scan_tab = self.create_email_scan_tab()
        self.update_tab = self.create_update_tab()
        self.settings_tab = self.create_settings_tab()
        self.quarantine_tab = self.create_quarantine_tab()
        self.config_editor_tab = self.create_config_editor_tab()
        
        self.tabs.addTab(self.scan_tab, self.tr("Scan"))
        self.tabs.addTab(self.email_scan_tab, self.tr("Email Scan"))
        self.tabs.addTab(self.update_tab, self.tr("Update"))
        self.tabs.addTab(self.settings_tab, self.tr("Settings"))
        self.tabs.addTab(self.quarantine_tab, self.tr("Quarantine"))
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
                self.tabs.setTabText(0, self.tr("Scan"))
                self.tabs.setTabText(1, self.tr("Email Scan"))
                self.tabs.setTabText(2, self.tr("Update"))
                self.tabs.setTabText(3, self.tr("Settings"))
                self.tabs.setTabText(4, self.tr("Quarantine"))
                self.tabs.setTabText(5, self.tr("Config Editor"))
            
            # Update status bar
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(self.tr("Ready"))
            
        except Exception as e:
            logger.error(f"Error retranslating UI: {e}")
    
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
        
        self.enable_smart_scanning = QCheckBox(self.tr("Enable smart scanning (skip known safe files)"))
        self.enable_smart_scanning.setChecked(False)
        self.enable_smart_scanning.setToolTip(self.tr("Use hash database to skip files that have been previously scanned and confirmed safe"))
        options_layout.addWidget(self.enable_smart_scanning)
        
        # Advanced scan options
        self.scan_archives = QCheckBox(self.tr("Scan archives (zip, rar, etc.)"))
        self.scan_archives.setChecked(True)
        options_layout.addWidget(self.scan_archives)
        
        self.scan_pua = QCheckBox(self.tr("Scan potentially unwanted applications (PUA)"))
        self.scan_pua.setChecked(False)
        self.scan_pua.setToolTip(self.tr("Enable scanning for potentially unwanted applications"))
        options_layout.addWidget(self.scan_pua)
        
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
        
        # Report buttons
        self.save_report_btn = QPushButton(self.tr("Save Report"))
        self.save_report_btn.setEnabled(False)
        self.save_report_btn.clicked.connect(self.save_scan_report)
        button_layout.addWidget(self.save_report_btn)
        
        self.view_quarantine_btn = QPushButton(self.tr("View Quarantine"))
        self.view_quarantine_btn.clicked.connect(self.show_quarantine_dialog)
        button_layout.addWidget(self.view_quarantine_btn)
        
        # Add all to main layout
        layout.addWidget(target_group)
        layout.addWidget(options_group)
        layout.addWidget(output_group)
        layout.addWidget(self.progress)
        layout.addLayout(button_layout)
        
        return tab
    
    def create_email_scan_tab(self):
        """Create the email scanning tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Email file selection
        email_group = QGroupBox(self.tr("Email Files to Scan"))
        email_layout = QVBoxLayout()

        # File list for multiple email files
        self.email_files_list = QListWidget()
        self.email_files_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.email_files_list.setMaximumHeight(150)
        email_layout.addWidget(self.email_files_list)

        # Buttons for file management
        file_btn_layout = QHBoxLayout()

        add_file_btn = QPushButton(self.tr("Add Email File"))
        add_file_btn.clicked.connect(self.add_email_file)
        file_btn_layout.addWidget(add_file_btn)

        remove_file_btn = QPushButton(self.tr("Remove Selected"))
        remove_file_btn.clicked.connect(self.remove_email_file)
        file_btn_layout.addWidget(remove_file_btn)

        clear_files_btn = QPushButton(self.tr("Clear All"))
        clear_files_btn.clicked.connect(self.clear_email_files)
        file_btn_layout.addWidget(clear_files_btn)

        email_layout.addLayout(file_btn_layout)
        email_group.setLayout(email_layout)

        # Scan options
        options_group = QGroupBox(self.tr("Scan Options"))
        options_layout = QVBoxLayout()

        self.scan_email_attachments = QCheckBox(self.tr("Scan email attachments"))
        self.scan_email_attachments.setChecked(True)
        options_layout.addWidget(self.scan_email_attachments)

        self.scan_email_content = QCheckBox(self.tr("Scan email content for suspicious patterns"))
        self.scan_email_content.setChecked(True)
        options_layout.addWidget(self.scan_email_content)

        options_group.setLayout(options_layout)

        # Output
        output_group = QGroupBox(self.tr("Scan Output"))
        output_layout = QVBoxLayout()

        self.email_output = QTextEdit()
        self.email_output.setReadOnly(True)
        output_layout.addWidget(self.email_output)

        output_group.setLayout(output_layout)

        # Progress
        self.email_progress = QProgressBar()

        # Buttons
        button_layout = QHBoxLayout()

        self.start_email_scan_btn = QPushButton(self.tr("Start Email Scan"))
        self.start_email_scan_btn.clicked.connect(self.start_email_scan)
        button_layout.addWidget(self.start_email_scan_btn)

        self.stop_email_scan_btn = QPushButton(self.tr("Stop"))
        self.stop_email_scan_btn.setEnabled(False)
        self.stop_email_scan_btn.clicked.connect(self.stop_email_scan)
        button_layout.addWidget(self.stop_email_scan_btn)

        self.save_email_report_btn = QPushButton(self.tr("Save Report"))
        self.save_email_report_btn.setEnabled(False)
        self.save_email_report_btn.clicked.connect(self.save_email_report)
        button_layout.addWidget(self.save_email_report_btn)

        # Add all to main layout
        layout.addWidget(email_group)
        layout.addWidget(options_group)
        layout.addWidget(output_group)
        layout.addWidget(self.email_progress)
        layout.addLayout(button_layout)

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
        
        # Scan settings
        scan_group = QGroupBox(self.tr("Scan Settings"))
        scan_layout = QVBoxLayout()
        
        # Basic scan options
        basic_options = QGroupBox(self.tr("Basic Options"))
        basic_layout = QVBoxLayout()
        
        self.scan_archives = QCheckBox(self.tr("Scan archives (zip, rar, etc.)"))
        self.scan_archives.setChecked(True)
        basic_layout.addWidget(self.scan_archives)
        
        self.scan_heuristics = QCheckBox(self.tr("Enable heuristic analysis"))
        self.scan_heuristics.setChecked(True)
        basic_layout.addWidget(self.scan_heuristics)
        
        self.scan_pua = QCheckBox(self.tr("Scan potentially unwanted applications"))
        self.scan_pua.setChecked(False)
        basic_layout.addWidget(self.scan_pua)
        
        self.enable_quarantine = QCheckBox(self.tr("Auto-quarantine infected files"))
        self.enable_quarantine.setChecked(True)
        basic_layout.addWidget(self.enable_quarantine)
        
        basic_options.setLayout(basic_layout)
        scan_layout.addWidget(basic_options)
        
        # Performance settings
        perf_options = QGroupBox(self.tr("Performance Settings"))
        perf_layout = QFormLayout()
        
        self.max_file_size = QLineEdit()
        self.max_file_size.setText("100")
        self.max_file_size.setToolTip(self.tr("Maximum file size to scan (MB)"))
        perf_layout.addRow(self.tr("Max file size (MB):"), self.max_file_size)
        
        self.max_scan_time = QLineEdit()
        self.max_scan_time.setText("300")
        self.max_scan_time.setToolTip(self.tr("Maximum scan time per file (seconds)"))
        perf_layout.addRow(self.tr("Max scan time (sec):"), self.max_scan_time)
        
        perf_options.setLayout(perf_layout)
        scan_layout.addWidget(perf_options)
        
        # File patterns
        pattern_group = QGroupBox(self.tr("File Patterns"))
        pattern_layout = QFormLayout()
        
        self.exclude_patterns = QLineEdit()
        self.exclude_patterns.setText("*.log,*.tmp,*.cache")
        self.exclude_patterns.setToolTip(self.tr("Comma-separated patterns to exclude (e.g., *.log,*.tmp)"))
        pattern_layout.addRow(self.tr("Exclude patterns:"), self.exclude_patterns)
        
        self.include_patterns = QLineEdit()
        self.include_patterns.setText("*")
        self.include_patterns.setToolTip(self.tr("Comma-separated patterns to include (default: *)"))
        pattern_layout.addRow(self.tr("Include patterns:"), self.include_patterns)
        
        pattern_group.setLayout(pattern_layout)
        scan_layout.addWidget(pattern_group)
        
        scan_group.setLayout(scan_layout)
        
        # Save button
        save_btn = QPushButton(self.tr("Save Settings"))
        save_btn.clicked.connect(self.save_settings)
        
        # Add to main layout
        layout.addWidget(path_group)
        layout.addWidget(scan_group)
        layout.addStretch()
        layout.addWidget(save_btn)
        
        return tab
    
    def create_quarantine_tab(self):
        """Create the quarantine management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Quarantine statistics
        stats_group = QGroupBox(self.tr("Quarantine Statistics"))
        stats_layout = QVBoxLayout()
        
        self.quarantine_stats_text = QTextEdit()
        self.quarantine_stats_text.setReadOnly(True)
        self.quarantine_stats_text.setMaximumHeight(150)
        stats_layout.addWidget(self.quarantine_stats_text)
        
        refresh_btn = QPushButton(self.tr("Refresh Stats"))
        refresh_btn.clicked.connect(self.refresh_quarantine_stats)
        stats_layout.addWidget(refresh_btn)
        
        stats_group.setLayout(stats_layout)
        
        # Quarantine file list
        files_group = QGroupBox(self.tr("Quarantined Files"))
        files_layout = QVBoxLayout()
        
        self.quarantine_files_list = QListWidget()
        self.quarantine_files_list.setSelectionMode(QAbstractItemView.MultiSelection)
        files_layout.addWidget(self.quarantine_files_list)
        
        # File management buttons
        file_btn_layout = QHBoxLayout()
        
        restore_btn = QPushButton(self.tr("Restore Selected"))
        restore_btn.clicked.connect(self.restore_selected_files)
        file_btn_layout.addWidget(restore_btn)
        
        delete_btn = QPushButton(self.tr("Delete Selected"))
        delete_btn.clicked.connect(self.delete_selected_files)
        file_btn_layout.addWidget(delete_btn)
        
        # Bulk operations
        bulk_btn_layout = QHBoxLayout()
        
        restore_all_btn = QPushButton(self.tr("Restore All"))
        restore_all_btn.clicked.connect(self.restore_all_files)
        bulk_btn_layout.addWidget(restore_all_btn)
        
        delete_all_btn = QPushButton(self.tr("Delete All"))
        delete_all_btn.clicked.connect(self.delete_all_files)
        bulk_btn_layout.addWidget(delete_all_btn)
        
        cleanup_btn = QPushButton(self.tr("Cleanup (30+ days)"))
        cleanup_btn.clicked.connect(self.cleanup_old_files)
        bulk_btn_layout.addWidget(cleanup_btn)
        
        files_layout.addLayout(file_btn_layout)
        files_layout.addLayout(bulk_btn_layout)
        
        export_btn = QPushButton(self.tr("Export List"))
        export_btn.clicked.connect(self.export_quarantine_list)
        file_btn_layout.addWidget(export_btn)
        
        # Add to main layout
        layout.addWidget(stats_group)
        layout.addWidget(files_group)
        
        # Initial refresh
        self.refresh_quarantine_stats()
        self.refresh_quarantine_files()
        
        return tab
    
    def refresh_quarantine_stats(self):
        """Refresh the quarantine statistics display."""
        try:
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
            self.quarantine_stats_text.setPlainText(f"Error loading quarantine statistics: {str(e)}")
    
    def refresh_quarantine_files(self):
        """Refresh the list of quarantined files."""
        try:
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
        """Start the ClamAV scan."""
        target = self.target_input.text()
        if not target:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Please select a target to scan"))
            return
        
        # Validate ClamAV installation first
        is_installed, status_msg, version_info = self.clamav_validator.check_clamav_installation()
        
        if not is_installed:
            # Show detailed error message with installation guidance
            error_msg = f"{status_msg}\n\n{self.clamav_validator.get_installation_guidance()}"
            QMessageBox.critical(self, self.tr("ClamAV Not Found"), error_msg)
            
            # Also try to suggest auto-detection of clamscan path
            suggested_path = self.clamav_validator.find_clamscan()
            if suggested_path and suggested_path != self.clamscan_path.text().strip():
                reply = QMessageBox.question(
                    self, self.tr("Auto-detect ClamAV?"),
                    self.tr(f"Would you like to use the detected path: {suggested_path}?"),
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.clamscan_path.setText(suggested_path)
                    return  # Return to let user try again
            
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
        
        # ClamAV is installed, proceed with scan
        logger.info(f"Starting scan with ClamAV at: {status_msg}")
        
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
            
        # Add scan options based on settings
        if self.scan_archives.isChecked():
            cmd.append("-a")  # Scan archives
        
        if self.scan_heuristics.isChecked():
            cmd.append("--heuristic-alerts")
            
        if self.scan_pua.isChecked():
            cmd.append("--detect-pua")
            
        # Add performance settings
        try:
            max_file_size_mb = int(self.max_file_size.text())
            if max_file_size_mb > 0:
                cmd.extend(['--max-filesize', f'{max_file_size_mb}M'])
        except (ValueError, AttributeError):
            pass
            
        try:
            max_scan_time = int(self.max_scan_time.text())
            if max_scan_time > 0:
                cmd.extend(['--max-scantime', str(max_scan_time)])
        except (ValueError, AttributeError):
            pass
            
        # Add file pattern options
        exclude_patterns = self.exclude_patterns.text().strip()
        if exclude_patterns and exclude_patterns != "*":
            for pattern in exclude_patterns.split(','):
                pattern = pattern.strip()
                if pattern:
                    cmd.extend(['--exclude', pattern])
                    
        include_patterns = self.include_patterns.text().strip()
        if include_patterns and include_patterns != "*":
            for pattern in include_patterns.split(','):
                pattern = pattern.strip()
                if pattern:
                    cmd.extend(['--include', pattern])
        
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
        
        # ClamAV is installed, proceed with scan
        logger.info(f"Starting scan with ClamAV at: {status_msg}")
        
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
            
        # Add scan options based on settings
        if self.scan_archives.isChecked():
            cmd.append("-a")  # Scan archives
        
        if self.scan_heuristics.isChecked():
            cmd.append("--heuristic-alerts")
            
        if self.scan_pua.isChecked():
            cmd.append("--detect-pua")
            
        # Add performance settings
        try:
            max_file_size_mb = int(self.max_file_size.text())
            if max_file_size_mb > 0:
                cmd.extend(['--max-filesize', f'{max_file_size_mb}M'])
        except (ValueError, AttributeError):
            pass
            
        try:
            max_scan_time = int(self.max_scan_time.text())
            if max_scan_time > 0:
                cmd.extend(['--max-scantime', str(max_scan_time)])
        except (ValueError, AttributeError):
            pass
            
        # Add file pattern options
        exclude_patterns = self.exclude_patterns.text().strip()
        if exclude_patterns and exclude_patterns != "*":
            for pattern in exclude_patterns.split(','):
                pattern = pattern.strip()
                if pattern:
                    cmd.extend(['--exclude', pattern])
                    
        include_patterns = self.include_patterns.text().strip()
        if include_patterns and include_patterns != "*":
            for pattern in include_patterns.split(','):
                pattern = pattern.strip()
                if pattern:
                    cmd.extend(['--include', pattern])
        
        # Add target and output options
        cmd.extend([target, "--verbose", "--stdout"])
        
        # Use error recovery for scan operations
        try:
            # Start the scan in a separate thread with error recovery
            self.scan_thread = ScanThread(cmd, enable_smart_scanning=self.enable_smart_scanning.isChecked())
            self.scan_thread.update_output.connect(self.update_scan_output)
            self.scan_thread.update_progress.connect(self.update_progress)
            self.scan_thread.update_stats.connect(self.update_scan_stats)
            self.scan_thread.finished.connect(self.scan_finished)
            self.scan_thread.cancelled.connect(self.scan_cancelled)
            
            # Update UI
            self.scan_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.output.clear()
            
            # Configure progress bar
            if hasattr(self, 'progress'):
                self.progress.setRange(0, 100)
                self.progress.setValue(0)
                self.progress.setFormat("%p%")
                self.progress.setAlignment(Qt.AlignCenter)
                self.progress.setTextVisible(True)
            
            # Start the thread
            self.scan_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting scan: {e}")
            QMessageBox.critical(self, self.tr("Scan Error"), 
                               self.tr(f"Failed to start scan: {str(e)}"))
    
    def stop_scan(self):
        """Stop the current scan."""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.cancel()
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
            
            # Only update if the value has changed significantly
            current_value = self.progress.value()
            if abs(value - current_value) > 2 or value in (0, 100):
                self.progress.setValue(value)
                
                # Force UI update
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
        # Disconnect any existing connections to avoid duplicates
        if hasattr(self.virus_db_updater, 'signals'):
            self.virus_db_updater.signals.disconnect_all()

        # Use error recovery for database updates
        try:
            # Use enhanced update thread with error recovery
            self.update_thread = EnhancedUpdateThread(self.virus_db_updater)
            self.update_thread.update_output.connect(self.update_update_output)
            self.update_thread.update_progress.connect(self.update_progress)
            self.update_thread.finished.connect(self.update_finished)

            # Clear and update UI
            self.update_output.clear()

            # Get freshclam path from settings if available
            freshclam_path = None
            if hasattr(self, 'freshclam_path') and self.freshclam_path.text().strip():
                freshclam_path = self.freshclam_path.text().strip()

            if freshclam_path:
                self.virus_db_updater = EnhancedVirusDBUpdater(freshclam_path)

            # Start the enhanced update
            self.update_thread.start()

        except Exception as e:
            logger.error(f"Error starting database update: {e}")
            QMessageBox.critical(self, self.tr("Update Error"),
                               self.tr(f"Failed to start database update: {str(e)}"))
    
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
        if success:
            self.status_bar.showMessage(self.tr("Database updated successfully"))
            if hasattr(self, 'progress'):
                self.progress.setValue(100)
            QMessageBox.information(self, self.tr("Success"),
                                 self.tr(f"Virus database updated successfully.\n\n{message}"))

            # Clean up old backups
            try:
                self.virus_db_updater.cleanup_old_backups(7)  # Keep 7 days of backups
            except:
                pass
        else:
            self.status_bar.showMessage(self.tr("Database update failed"))
            QMessageBox.warning(self, self.tr("Warning"),
                             self.tr(f"Virus database update failed. Please check the logs for details.\n\n{message}"))
    
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
            'enable_smart_scanning': self.enable_smart_scanning.isChecked()
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
        if 'enable_smart_scanning' in scan_settings:
            self.enable_smart_scanning.setChecked(scan_settings.get('enable_smart_scanning', False))
        
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


class ScanThread(QThread):
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
    
    def terminate(self):
        """Terminate the process."""
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()
