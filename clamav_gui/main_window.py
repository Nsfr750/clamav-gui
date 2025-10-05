"""Main window for the ClamAV GUI application."""
import os
import subprocess
import logging
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QMessageBox, QApplication,
                             QStatusBar, QProgressBar, QSizePolicy, QMenuBar, QMenu,
                             QDialog, QTextEdit, QComboBox, QLineEdit, QCheckBox, QGroupBox,
                             QScrollArea, QFrame, QSplitter, QToolBar, QStyle, QInputDialog,
                             QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem, QHeaderView,
                             QAbstractItemView, QTableWidget, QTableWidgetItem, QToolButton, QStyleFactory)
from PySide6.QtCore import Qt, QTimer, QSize, QThread, Signal, QObject, QEvent, QSettings, QPoint, QByteArray, QBuffer, QIODevice, QProcess, QProcessEnvironment, QStandardPaths, QUrl, Slot
from PySide6.QtGui import (QIcon, QPixmap, QFont, QColor, QTextCursor, QDesktopServices, 
                        QAction, QKeySequence, QTextCharFormat, QTextDocument, QTextFormat, 
                        QSyntaxHighlighter, QTextBlockUserData, QTextBlock, QPainter, QPalette, 
                        FontMetrics, QGuiApplication, QClipboard, QImage, QMovie, QPixmap, QRegion)
from clamav_gui.ui import check_for_updates

# Import language manager
from clamav_gui.lang.lang_manager import SimpleLanguageManager

# Setup logger
{{ ... }}
logger = logging.getLogger(__name__)

class ClamAVGUI(QMainWindow):
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
        
        # Set up language manager
        self.lang_manager = lang_manager or SimpleLanguageManager()
        
        # Connect language changed signal
        if hasattr(self.lang_manager, 'language_changed'):
            self.lang_manager.language_changed.connect(self.retranslate_ui)
        
        self.setWindowTitle("ClamAV GUI")
        self.setMinimumSize(800, 600)
        
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
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        self.file_menu = menubar.addMenu(self.tr("&File"))
        
        # Add menu items
        self.exit_action = QAction(self.tr("E&xit"), self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        
        # Tools menu
        self.tools_menu = menubar.addMenu(self.tr("&Tools"))
        
        # Check for updates action
        self.check_updates_action = QAction(self.tr("Check for &Updates..."), self)
        self.check_updates_action.triggered.connect(self.check_for_updates)
        self.tools_menu.addAction(self.check_updates_action)
        
        # Language menu
        self.language_menu = menubar.addMenu(self.tr("&Language"))
        self.language_group = None
        self.setup_language_menu()
        
        # Help menu
        self.help_menu = menubar.addMenu(self.tr("&Help"))
        
        self.help_action = QAction(self.tr("&Help"), self)
        self.help_action.setShortcut("F1")
        self.help_action.triggered.connect(show_help)
        self.help_menu.addAction(self.help_action)
        
        self.help_menu.addSeparator()
        
        self.about_action = QAction(self.tr("&About"), self)
        self.about_action.triggered.connect(show_about)
        self.help_menu.addAction(self.about_action)
        
        self.sponsor_action = QAction(self.tr("&Support the Project"), self)
        self.sponsor_action.triggered.connect(show_sponsor)
        self.help_menu.addAction(self.sponsor_action)
    
    def setup_language_menu(self):
        """Set up the language selection menu."""
        if not hasattr(self, 'lang_manager') or not self.lang_manager:
            return
            
        # Clear existing actions
        self.language_menu.clear()
        
        # Create a new action group for language selection
        self.language_group = QActionGroup(self)
        self.language_group.setExclusive(True)
        
        # Add available languages
        for lang_code, lang_name in self.lang_manager.available_languages.items():
            action = QAction(lang_name, self, checkable=True)
            action.setData(lang_code)
            action.triggered.connect(self.change_language)
            self.language_menu.addAction(action)
            self.language_group.addAction(action)
            
            # Check current language
            if lang_code == self.lang_manager.current_lang:
                action.setChecked(True)
    
    def change_language(self):
        """Change the application language."""
        if not hasattr(self, 'language_group') or not self.language_group.checkedAction():
            return
            
        lang_code = self.language_group.checkedAction().data()
        if lang_code and self.lang_manager.set_language(lang_code):
            logger.info(f"Language changed to {lang_code}")
            
            # Save language preference
            if not hasattr(self, 'current_settings'):
                self.current_settings = {}
            self.current_settings['language'] = lang_code
            self.settings.save_settings(self.current_settings)
    
    def retranslate_ui(self):
        """Retranslate the UI when language changes."""
        if not hasattr(self, 'lang_manager') or not self.lang_manager:
            return
            
        try:
            # Update window title
            self.setWindowTitle(self.tr("ClamAV GUI"))
            
            # Update menu bar
            self.file_menu.setTitle(self.tr("&File"))
            self.tools_menu.setTitle(self.tr("&Tools"))
            self.help_menu.setTitle(self.tr("&Help"))
            self.language_menu.setTitle(self.tr("&Language"))
            
            # Update menu actions
            self.exit_action.setText(self.tr("E&xit"))
            self.check_updates_action.setText(self.tr("Check for &Updates..."))
            self.help_action.setText(self.tr("&Help"))
            self.about_action.setText(self.tr("&About"))
            self.sponsor_action.setText(self.tr("&Support the Project"))
            
            # Update tab names
            if hasattr(self, 'tabs'):
                self.tabs.setTabText(0, self.tr("Scan"))
                self.tabs.setTabText(1, self.tr("Update"))
                self.tabs.setTabText(2, self.tr("Settings"))
                self.tabs.setTabText(3, self.tr("Config Editor"))
            
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
        
        # Build the command
        cmd = ["clamscan", "-r"] if self.recursive_scan.isChecked() else ["clamscan"]
        if self.heuristic_scan.isChecked():
            cmd.append("--heuristic")
        cmd.append(target)
        
        # Start the scan in a separate thread
        self.scan_thread = ScanThread(cmd)
        self.scan_thread.update_output.connect(self.update_scan_output)
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
            self.status_bar.showMessage(self.tr("Scan completed successfully"))
        else:
            self.status_bar.showMessage(self.tr("Scan completed with errors"))
    
    def update_database(self):
        """Update the ClamAV virus database."""
        cmd = ["freshclam", "--verbose"]
        
        # Start the update in a separate thread
        self.update_thread = UpdateThread(cmd)
        self.update_thread.update_output.connect(self.update_update_output)
        self.update_thread.finished.connect(self.update_finished)
        
        # Update UI
        self.update_output.clear()
        
        # Start the thread
        self.update_thread.start()
    
    def update_update_output(self, text):
        """Update the update output with new text."""
        self.update_output.append(text)
    
    def update_finished(self, exit_code, status):
        """Handle update completion."""
        if exit_code == 0:
            self.status_bar.showMessage(self.tr("Database updated successfully"))
        else:
            self.status_bar.showMessage(self.tr("Database update failed"))
    
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


class ScanThread(QThread):
    """Thread for running ClamAV scans."""
    update_output = Signal(str)
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
