"""Config Editor tab for ClamAV GUI application."""
import os
import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QTextEdit, QComboBox,
                             QFileDialog, QMessageBox, QSplitter)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class ConfigEditorTab(QWidget):
    """Config Editor tab widget for editing ClamAV configuration files."""

    def __init__(self, parent=None):
        """Initialize the config editor tab.

        Args:
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.parent = parent  # Reference to main window
        self.current_config_file = None
        self.config_modified = False
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

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
        self.on_config_selection_changed()

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
