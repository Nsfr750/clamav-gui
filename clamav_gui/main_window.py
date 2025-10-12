"""Main window for the ClamAV GUI application."""
import os
import subprocess
import logging
import time
from pathlib import Path
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
        self.virus_db_updater = VirusDBUpdater()
        self.clamav_validator = ClamAVValidator()
        self.scan_report_generator = ScanReportGenerator()
        self.quarantine_manager = QuarantineManager()
        
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
        self.update_tab = self.create_update_tab()
        self.settings_tab = self.create_settings_tab()
        self.quarantine_tab = self.create_quarantine_tab()
        self.config_editor_tab = self.create_config_editor_tab()
        
        self.tabs.addTab(self.scan_tab, self.tr("Scan"))
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
                self.tabs.setTabText(1, self.tr("Update"))
                self.tabs.setTabText(2, self.tr("Settings"))
                self.tabs.setTabText(3, self.tr("Quarantine"))
                self.tabs.setTabText(4, self.tr("Config Editor"))
            
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
        
        # Quarantine options
        self.enable_quarantine = QCheckBox(self.tr("Auto-quarantine infected files"))
        self.enable_quarantine.setChecked(True)
        self.enable_quarantine.setToolTip(self.tr("Automatically move infected files to quarantine"))
        options_layout.addWidget(self.enable_quarantine)
        
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
        self.quarantine_files_list.setSelectionMode(QAbstractItemView.SingleSelection)
        files_layout.addWidget(self.quarantine_files_list)
        
        # File management buttons
        file_btn_layout = QHBoxLayout()
        
        restore_btn = QPushButton(self.tr("Restore Selected"))
        restore_btn.clicked.connect(self.restore_selected_file)
        file_btn_layout.addWidget(restore_btn)
        
        delete_btn = QPushButton(self.tr("Delete Selected"))
        delete_btn.clicked.connect(self.delete_selected_file)
        file_btn_layout.addWidget(delete_btn)
        
        export_btn = QPushButton(self.tr("Export List"))
        export_btn.clicked.connect(self.export_quarantine_list)
        file_btn_layout.addWidget(export_btn)
        
        files_layout.addLayout(file_btn_layout)
        files_group.setLayout(files_layout)
        
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
            QMessageBox.information(
                self, self.tr("Restore"),
                self.tr("File restoration is not yet fully implemented.\n"
                       "This feature will be available in a future update.")
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
            QMessageBox.information(
                self, self.tr("Delete"),
                self.tr("File deletion is not yet fully implemented.\n"
                       "This feature will be available in a future update.")
            )
    
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
        target = QFileDialog.getExistingDirectory(self, self.tr("Select Directory"))
        if target:
            self.target_input.setText(target)
    
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
        
        # Start the scan in a separate thread
        self.scan_thread = ScanThread(cmd)
        self.scan_thread.update_output.connect(self.update_scan_output)
        self.scan_thread.update_progress.connect(self.update_progress)
        self.scan_thread.finished.connect(self.scan_finished)
        
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
    
    def stop_scan(self):
        """Stop the current scan."""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.terminate()
            self.scan_thread.wait()
            self.scan_finished(1, 1)  # Signal error
    
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
            'clamscan_path': self.clamscan_path.text(),
            'scan_archives': self.scan_archives.isChecked(),
            'scan_heuristics': self.scan_heuristics.isChecked(),
            'scan_pua': self.scan_pua.isChecked(),
            'auto_quarantine': self.enable_quarantine.isChecked(),
            'max_file_size': self.max_file_size.text(),
            'max_scan_time': self.max_scan_time.text(),
            'exclude_patterns': self.exclude_patterns.text(),
            'include_patterns': self.include_patterns.text()
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
            total_files = 0
            processed_files = 0
            last_progress = 0
            start_time = time.time()
            
            # First, count total files if possible
            if 'clamscan' in self.command[0].lower() and len(self.command) > 1:
                try:
                    # Try to count files in the target directory
                    target = self.command[-1]
                    if os.path.isdir(target):
                        # Use a more efficient method to count files
                        total_files = sum(1 for _ in Path(target).rglob('*') if _.is_file())
                        self.update_output.emit(f"Found {total_files} files to scan")
                    elif os.path.isfile(target):
                        total_files = 1
                except Exception as e:
                    self.update_output.emit(f"Could not count files: {str(e)}")
            
            # Emit initial progress
            self.update_progress.emit(0)
            
            # Buffer for partial lines
            buffer = ""
            last_update = time.time()
            
            while not self.process.waitForFinished(100):  # Check every 100ms
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
                    
                    # Update progress for each scanned file
                    if 'Scanned file:' in line:
                        processed_files += 1
                        
                        # Only update progress at most once per second to avoid UI freezes
                        current_time = time.time()
                        if current_time - last_update >= 0.1:  # Update at most 10 times per second
                            if total_files > 0:
                                progress = min(99, int((processed_files / total_files) * 100))
                            else:
                                # If we don't know the total, use a simple increment
                                progress = min(99, processed_files % 100)
                            
                            if progress != last_progress:
                                self.update_progress.emit(progress)
                                last_progress = progress
                            
                            last_update = current_time
                    
                    # Try to get total files from summary if not already known
                    elif total_files == 0 and ' files, ' in line and 'infested files: ' in line:
                        try:
                            parts = line.split(' files, ')
                            if len(parts) > 1:
                                total_files = int(parts[0].split()[-1])
                                self.update_output.emit(f"Found {total_files} files to scan in total")
                        except (ValueError, IndexError):
                            pass
            
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
