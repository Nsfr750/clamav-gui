"""
Settings tab for ClamAV GUI application.
Provides interface for configuring ClamAV paths, scan settings, and database options.
"""
import os
import logging
from typing import Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QLineEdit, QFormLayout, QMessageBox, QSpinBox, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class SettingsTab(QWidget):
    """Settings tab for configuring ClamAV paths and scan options."""

    def __init__(self, parent=None):
        """Initialize the settings tab.

        Args:
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.parent = parent  # Reference to main window
        self.current_settings = {}

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # ClamAV Paths Section
        paths_group = QGroupBox(self.tr("ClamAV Executable Paths"))
        paths_layout = QFormLayout()

        self.clamd_path = QLineEdit()
        self.clamd_path.setPlaceholderText(self.tr("Path to clamd executable"))
        paths_layout.addRow(self.tr("ClamD Path:"), self.clamd_path)

        self.freshclam_path = QLineEdit()
        self.freshclam_path.setPlaceholderText(self.tr("Path to freshclam executable"))
        paths_layout.addRow(self.tr("FreshClam Path:"), self.freshclam_path)

        self.clamscan_path = QLineEdit()
        self.clamscan_path.setPlaceholderText(self.tr("Path to clamscan executable"))
        paths_layout.addRow(self.tr("ClamScan Path:"), self.clamscan_path)

        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)

        # Virus Database Section
        db_group = QGroupBox(self.tr("Virus Database Configuration"))
        db_layout = QFormLayout()

        # Database path (now editable with browse button)
        db_path_layout = QHBoxLayout()
        self.db_path_display = QLineEdit()
        self.db_path_display.setPlaceholderText(self.tr("Path to virus database directory"))
        db_path_layout.addWidget(self.db_path_display)

        browse_db_btn = QPushButton(self.tr("Browse..."))
        browse_db_btn.setMaximumWidth(80)
        browse_db_btn.clicked.connect(self.browse_database_path)
        browse_db_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                font-weight: bold;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        db_path_layout.addWidget(browse_db_btn)
        db_layout.addRow(self.tr("Database Location:"), db_path_layout)

        # Database update interval (days)
        self.db_update_interval = QSpinBox()
        self.db_update_interval.setRange(1, 30)
        self.db_update_interval.setValue(7)  # Default: weekly
        self.db_update_interval.setSuffix(self.tr(" days"))
        db_layout.addRow(self.tr("Auto-update interval:"), self.db_update_interval)

        # Custom database mirror (optional)
        self.db_mirror_url = QLineEdit()
        self.db_mirror_url.setPlaceholderText(self.tr("Custom database mirror URL (optional)"))
        db_layout.addRow(self.tr("Custom mirror:"), self.db_mirror_url)

        db_group.setLayout(db_layout)
        layout.addWidget(db_group)

        # Scanner Type Section
        scanner_group = QGroupBox(self.tr("Scanner Configuration"))
        scanner_layout = QVBoxLayout()

        # Scanner type selection
        self.scanner_type_combo = QComboBox()
        self.scanner_type_combo.addItem(self.tr("Integrated Scanner"), "integrated")
        self.scanner_type_combo.addItem(self.tr("ClamAV Scanner"), "clamav")
        self.scanner_type_combo.setToolTip(self.tr("Choose the scanning engine to use"))
        self.scanner_type_combo.currentTextChanged.connect(self.on_scanner_type_changed)
        scanner_layout.addWidget(QLabel(self.tr("Scanner Type:")))
        scanner_layout.addWidget(self.scanner_type_combo)

        # Scanner type description
        self.scanner_description = QLabel(self.tr(
            "• Integrated Scanner: Built-in scanning engine with enhanced features\n"
            "• ClamAV Scanner: Uses external ClamAV executable for maximum compatibility"
        ))
        self.scanner_description.setWordWrap(True)
        self.scanner_description.setStyleSheet("QLabel { color: #FFFE59; font-size: 11px; font-weight: bold; padding: 5px; }")
        scanner_layout.addWidget(self.scanner_description)

        scanner_group.setLayout(scanner_layout)
        layout.addWidget(scanner_group)
        scan_group = QGroupBox(self.tr("Default Scan Settings"))
        scan_layout = QVBoxLayout()

        # Basic scan options
        basic_options = QGroupBox(self.tr("Basic Options"))
        basic_layout = QVBoxLayout()

        self.default_scan_archives = QCheckBox(self.tr("Scan archives by default"))
        self.default_scan_archives.setChecked(True)
        basic_layout.addWidget(self.default_scan_archives)

        self.default_scan_heuristics = QCheckBox(self.tr("Enable heuristic analysis by default"))
        self.default_scan_heuristics.setChecked(True)
        basic_layout.addWidget(self.default_scan_heuristics)

        self.default_scan_pua = QCheckBox(self.tr("Scan PUA by default"))
        self.default_scan_pua.setChecked(False)
        basic_layout.addWidget(self.default_scan_pua)

        self.default_enable_quarantine = QCheckBox(self.tr("Auto-quarantine infected files by default"))
        self.default_enable_quarantine.setChecked(True)
        basic_layout.addWidget(self.default_enable_quarantine)

        basic_options.setLayout(basic_layout)
        scan_layout.addWidget(basic_options)

        # Performance settings
        perf_options = QGroupBox(self.tr("Performance Settings"))
        perf_layout = QFormLayout()

        self.default_max_file_size = QLineEdit()
        self.default_max_file_size.setText("100")
        self.default_max_file_size.setToolTip(self.tr("Maximum file size to scan (MB)"))
        perf_layout.addRow(self.tr("Max file size (MB):"), self.default_max_file_size)

        self.default_max_scan_time = QLineEdit()
        self.default_max_scan_time.setText("300")
        self.default_max_scan_time.setToolTip(self.tr("Maximum scan time per file (seconds)"))
        perf_layout.addRow(self.tr("Max scan time (sec):"), self.default_max_scan_time)

        perf_options.setLayout(perf_layout)
        scan_layout.addWidget(perf_options)

        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)

        # File Pattern Settings
        pattern_group = QGroupBox(self.tr("File Pattern Settings"))
        pattern_layout = QFormLayout()

        self.default_exclude_patterns = QLineEdit()
        self.default_exclude_patterns.setText("*.log,*.tmp,*.cache")
        self.default_exclude_patterns.setToolTip(self.tr("Comma-separated patterns to exclude"))
        pattern_layout.addRow(self.tr("Exclude patterns:"), self.default_exclude_patterns)

        self.default_include_patterns = QLineEdit()
        self.default_include_patterns.setText("*")
        self.default_include_patterns.setToolTip(self.tr("Comma-separated patterns to include"))
        pattern_layout.addRow(self.tr("Include patterns:"), self.default_include_patterns)

        pattern_group.setLayout(pattern_layout)
        layout.addWidget(pattern_group)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.save_settings_btn = QPushButton(self.tr("Save Settings"))
        self.save_settings_btn.clicked.connect(self.save_settings)
        self.save_settings_btn.setStyleSheet("""
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
        buttons_layout.addWidget(self.save_settings_btn)

        self.reset_settings_btn = QPushButton(self.tr("Reset to Defaults"))
        self.reset_settings_btn.clicked.connect(self.reset_settings)
        self.reset_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        """)
        buttons_layout.addWidget(self.reset_settings_btn)

        self.load_config_btn = QPushButton(self.tr("Load from Config"))
        self.load_config_btn.clicked.connect(self.load_from_config)
        self.load_config_btn.setStyleSheet("""
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
        buttons_layout.addWidget(self.load_config_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Load current settings
        self.load_settings()

        # Set initial scanner type visibility
        self.on_scanner_type_changed()

    def on_scanner_type_changed(self):
        """Handle scanner type selection change."""
        scanner_type = self.scanner_type_combo.currentData()
        is_clamav = scanner_type == "clamav"

        # Show/hide ClamAV paths section based on scanner type
        if hasattr(self, 'paths_group'):
            self.paths_group.setVisible(is_clamav)

        # Update description text based on selection
        if hasattr(self, 'scanner_description'):
            if is_clamav:
                self.scanner_description.setText(self.tr(
                    "• ClamAV Scanner: Uses external ClamAV executable for maximum compatibility\n"
                    "  Requires ClamAV to be installed on the system\n"
                    "  Database updates handled by ClamAV's freshclam utility"
                ))
            else:
                self.scanner_description.setText(self.tr(
                    "• Integrated Scanner: Built-in scanning engine with enhanced features\n"
                    "  Self-contained with embedded virus definitions\n"
                    "  Automatic updates and advanced threat detection"
                ))

    def browse_database_path(self):
        """Browse for virus database directory."""
        from PySide6.QtWidgets import QFileDialog

        current_path = self.db_path_display.text()
        if not current_path or current_path == self.get_database_path():
            # Start from the detected database path
            start_dir = self.get_database_path()
        else:
            start_dir = current_path

        db_path = QFileDialog.getExistingDirectory(
            self, self.tr("Select Virus Database Directory"),
            start_dir,
            QFileDialog.ShowDirsOnly
        )

        if db_path:
            self.db_path_display.setText(db_path)

    def get_database_path(self):
        """Get the current virus database path."""
        try:
            # First check if we have a custom database path set in the display field
            if hasattr(self, 'db_path_display') and self.db_path_display.text().strip():
                custom_path = self.db_path_display.text().strip()
                if custom_path and custom_path != self.tr("Unknown") and os.path.exists(custom_path):
                    return custom_path

            # Try to detect the default ClamAV database path
            try:
                import subprocess
                import sys

                # Try to run freshclam --info to get database path
                try:
                    result = subprocess.run(['freshclam', '--info'],
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'Database directory' in line:
                                db_path = line.split(':', 1)[-1].strip()
                                if db_path and os.path.exists(db_path):
                                    return db_path
                except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                    pass

                # Fallback: common ClamAV database paths
                common_paths = [
                    "C:\\ProgramData\\ClamAV\\db",
                    "C:\\ClamAV\\db",
                    "/var/lib/clamav",
                    "/usr/share/clamav",
                    os.path.expanduser("~/.clamav")
                ]

                for path in common_paths:
                    if os.path.exists(path):
                        return path

            except Exception as e:
                logger.warning(f"Error detecting database path: {e}")

            # Fallback to parent method if available
            if hasattr(self.parent, 'get_database_path'):
                return self.parent.get_database_path()
        except Exception as e:
            logger.warning(f"Error getting database path: {e}")
        return self.tr("Unknown")

    def save_settings(self):
        """Save current settings."""
        try:
            if not hasattr(self, 'current_settings'):
                self.current_settings = {}

            # Save ClamAV paths (only if using ClamAV scanner)
            scanner_type = self.scanner_type_combo.currentData()
            if scanner_type == "clamav":
                self.current_settings['clamd_path'] = self.clamd_path.text()
                self.current_settings['freshclam_path'] = self.freshclam_path.text()
                self.current_settings['clamscan_path'] = self.clamscan_path.text()
            else:
                # Clear ClamAV paths when using integrated scanner
                self.current_settings['clamd_path'] = ""
                self.current_settings['freshclam_path'] = ""
                self.current_settings['clamscan_path'] = ""

            # Save database settings
            self.current_settings['db_update_interval'] = self.db_update_interval.value()
            self.current_settings['db_mirror_url'] = self.db_mirror_url.text()
            db_path = self.db_path_display.text().strip()
            if db_path and db_path != self.tr("Unknown"):
                # Validate the database path exists
                if os.path.exists(db_path) and os.path.isdir(db_path):
                    self.current_settings['db_path'] = db_path
                else:
                    # Show warning but still save (user might want to set a path that doesn't exist yet)
                    reply = QMessageBox.question(
                        self, self.tr("Invalid Database Path"),
                        self.tr(f"The specified database path does not exist:\n{db_path}\n\nDo you want to save it anyway?"),
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.current_settings['db_path'] = db_path
                    else:
                        # Don't save the invalid path
                        self.current_settings['db_path'] = ""
            else:
                self.current_settings['db_path'] = ""

            # Save scanner type
            self.current_settings['scanner_type'] = self.scanner_type_combo.currentData()

            # Save scan settings - use hasattr to check if attributes exist
            if hasattr(self, 'default_scan_archives'):
                self.current_settings['scan_archives'] = self.default_scan_archives.isChecked()
            if hasattr(self, 'default_scan_heuristics'):
                self.current_settings['scan_heuristics'] = self.default_scan_heuristics.isChecked()
            if hasattr(self, 'default_scan_pua'):
                self.current_settings['scan_pua'] = self.default_scan_pua.isChecked()
            if hasattr(self, 'default_enable_quarantine'):
                self.current_settings['enable_quarantine'] = self.default_enable_quarantine.isChecked()
            if hasattr(self, 'default_max_file_size'):
                self.current_settings['max_file_size'] = self.default_max_file_size.text()
            if hasattr(self, 'default_max_scan_time'):
                self.current_settings['max_scan_time'] = self.default_max_scan_time.text()
            if hasattr(self, 'default_exclude_patterns'):
                self.current_settings['exclude_patterns'] = self.default_exclude_patterns.text()
            if hasattr(self, 'default_include_patterns'):
                self.current_settings['include_patterns'] = self.default_include_patterns.text()

            # Save to file
            if hasattr(self.parent, 'settings') and self.parent.settings:
                success = self.parent.settings.save_settings(self.current_settings)
                if success:
                    QMessageBox.information(self, self.tr("Success"),
                                          self.tr("Settings saved successfully!"))
                else:
                    QMessageBox.critical(self, self.tr("Error"),
                                       self.tr("Failed to save settings!"))
            else:
                QMessageBox.warning(self, self.tr("Warning"),
                                  self.tr("Settings manager not available"))

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, self.tr("Error"),
                               self.tr(f"Error saving settings: {str(e)}"))

    def reset_settings(self):
        """Reset settings to defaults."""
        reply = QMessageBox.question(
            self, self.tr("Reset Settings"),
            self.tr("Are you sure you want to reset all settings to defaults?\n\nThis action cannot be undone."),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Reset ClamAV paths (clear them since default is integrated scanner)
            self.clamd_path.clear()
            self.freshclam_path.clear()
            self.clamscan_path.clear()

            self.db_update_interval.setValue(7)
            self.db_mirror_url.clear()
            self.db_path_display.clear()

            # Reset scanner type to default (integrated)
            index = self.scanner_type_combo.findData("integrated")
            if index != -1:
                self.scanner_type_combo.setCurrentIndex(index)
            else:
                self.scanner_type_combo.setCurrentText(self.tr("Integrated Scanner"))

            # Reset scan settings - use hasattr to check if attributes exist
            if hasattr(self, 'default_scan_archives'):
                self.default_scan_archives.setChecked(True)
            if hasattr(self, 'default_scan_heuristics'):
                self.default_scan_heuristics.setChecked(True)
            if hasattr(self, 'default_scan_pua'):
                self.default_scan_pua.setChecked(False)
            if hasattr(self, 'default_enable_quarantine'):
                self.default_enable_quarantine.setChecked(True)
            if hasattr(self, 'default_max_file_size'):
                self.default_max_file_size.setText("100")
            if hasattr(self, 'default_max_scan_time'):
                self.default_max_scan_time.setText("300")
            if hasattr(self, 'default_exclude_patterns'):
                self.default_exclude_patterns.setText("*.log,*.tmp,*.cache")
            if hasattr(self, 'default_include_patterns'):
                self.default_include_patterns.setText("*")

            QMessageBox.information(self, self.tr("Reset Complete"),
                                  self.tr("Settings have been reset to defaults."))

    def load_from_config(self):
        """Load settings from config/settings.json file."""
        try:
            import json
            config_file = 'config/settings.json'

            if not os.path.exists(config_file):
                QMessageBox.warning(self, self.tr("Config Not Found"),
                                  self.tr(f"Configuration file not found:\n{config_file}"))
                return

            # Load settings from JSON file
            with open(config_file, 'r', encoding='utf-8') as f:
                json_settings = json.load(f)

            # Update form fields with loaded settings (only if using ClamAV scanner)
            current_scanner_type = json_settings.get('scanner_type', 'integrated')
            if current_scanner_type == "clamav":
                self.clamd_path.setText(json_settings.get('clamd_path', ''))
                self.freshclam_path.setText(json_settings.get('freshclam_path', ''))
                self.clamscan_path.setText(json_settings.get('clamscan_path', ''))
            else:
                # Clear ClamAV paths when using integrated scanner
                self.clamd_path.clear()
                self.freshclam_path.clear()
                self.clamscan_path.clear()

            # Update scan settings
            if hasattr(self, 'default_scan_archives'):
                self.default_scan_archives.setChecked(json_settings.get('scan_archives', True))
            if hasattr(self, 'default_scan_heuristics'):
                self.default_scan_heuristics.setChecked(json_settings.get('scan_heuristics', True))
            if hasattr(self, 'default_scan_pua'):
                self.default_scan_pua.setChecked(json_settings.get('scan_pua', False))

            if hasattr(self, 'default_max_file_size'):
                self.default_max_file_size.setText(str(json_settings.get('max_file_size', '100')))
            if hasattr(self, 'default_max_scan_time'):
                self.default_max_scan_time.setText(str(json_settings.get('max_scan_time', '300')))
            if hasattr(self, 'default_exclude_patterns'):
                self.default_exclude_patterns.setText(json_settings.get('exclude_patterns', '*.log,*.tmp,*.cache'))
            if hasattr(self, 'default_include_patterns'):
                self.default_include_patterns.setText(json_settings.get('include_patterns', '*'))

            # Update database settings (if they exist in the JSON file)
            if 'db_update_interval' in json_settings:
                self.db_update_interval.setValue(json_settings['db_update_interval'])
            if 'db_mirror_url' in json_settings:
                self.db_mirror_url.setText(json_settings['db_mirror_url'])
            if 'db_path' in json_settings:
                self.db_path_display.setText(json_settings['db_path'])

            # Update scanner type
            scanner_type = json_settings.get('scanner_type', 'integrated')
            if scanner_type == 'integrated':
                self.scanner_type_combo.setCurrentText(self.tr("Integrated Scanner"))
            elif scanner_type == 'clamav':
                self.scanner_type_combo.setCurrentText(self.tr("ClamAV Scanner"))

            # Update current settings
            self.current_settings.update(json_settings)

            QMessageBox.information(self, self.tr("Load Complete"),
                                  self.tr("Settings loaded successfully from config/settings.json!\n\n"
                                        "Don't forget to click 'Save Settings' to apply the changes."))

        except Exception as e:
            logger.error(f"Error loading settings from config: {e}")
            QMessageBox.critical(self, self.tr("Load Error"),
                               self.tr(f"Failed to load settings from config:\n\n{str(e)}"))

    def load_settings(self):
        """Load settings into the form."""
        try:
            if hasattr(self.parent, 'settings') and self.parent.settings:
                self.current_settings = self.parent.settings.load_settings() or {}

                # Load ClamAV paths (only if using ClamAV scanner)
                current_scanner_type = self.current_settings.get('scanner_type', 'integrated')
                if current_scanner_type == "clamav":
                    self.clamd_path.setText(self.current_settings.get('clamd_path', ''))
                    self.freshclam_path.setText(self.current_settings.get('freshclam_path', ''))
                    self.clamscan_path.setText(self.current_settings.get('clamscan_path', ''))
                else:
                    # Clear ClamAV paths when using integrated scanner
                    self.clamd_path.clear()
                    self.freshclam_path.clear()
                    self.clamscan_path.clear()

                # Load database settings
                if 'db_update_interval' in self.current_settings:
                    self.db_update_interval.setValue(self.current_settings['db_update_interval'])
                if 'db_mirror_url' in self.current_settings:
                    self.db_mirror_url.setText(self.current_settings['db_mirror_url'])
                if 'db_path' in self.current_settings and self.current_settings['db_path']:
                    self.db_path_display.setText(self.current_settings['db_path'])
                else:
                    # If no custom path saved, show the detected path
                    detected_path = self.get_database_path()
                    if detected_path and detected_path != self.tr("Unknown"):
                        self.db_path_display.setText(detected_path)

                # Load scanner type
                scanner_type = self.current_settings.get('scanner_type', 'integrated')
                if scanner_type == 'integrated':
                    self.scanner_type_combo.setCurrentText(self.tr("Integrated Scanner"))
                elif scanner_type == 'clamav':
                    self.scanner_type_combo.setCurrentText(self.tr("ClamAV Scanner"))

                # Load scan settings - use hasattr to check if attributes exist
                if hasattr(self, 'default_scan_archives'):
                    self.default_scan_archives.setChecked(self.current_settings.get('scan_archives', True))
                if hasattr(self, 'default_scan_heuristics'):
                    self.default_scan_heuristics.setChecked(self.current_settings.get('scan_heuristics', True))
                if hasattr(self, 'default_scan_pua'):
                    self.default_scan_pua.setChecked(self.current_settings.get('scan_pua', False))
                if hasattr(self, 'default_enable_quarantine'):
                    self.default_enable_quarantine.setChecked(self.current_settings.get('enable_quarantine', True))
                if hasattr(self, 'default_max_file_size'):
                    self.default_max_file_size.setText(str(self.current_settings.get('max_file_size', '100')))
                if hasattr(self, 'default_max_scan_time'):
                    self.default_max_scan_time.setText(str(self.current_settings.get('max_scan_time', '600')))
                if hasattr(self, 'default_exclude_patterns'):
                    self.default_exclude_patterns.setText(self.current_settings.get('exclude_patterns', '*.log,*.tmp,*.cache'))
                if hasattr(self, 'default_include_patterns'):
                    self.default_include_patterns.setText(self.current_settings.get('include_patterns', '*'))

        except Exception as e:
            logger.error(f"Error loading settings: {e}")

    def get_settings(self) -> Dict:
        """Get the current settings from the form."""
        settings = {}

        # Get ClamAV paths (only if using ClamAV scanner)
        current_scanner_type = self.scanner_type_combo.currentData()
        if current_scanner_type == "clamav":
            settings['clamd_path'] = self.clamd_path.text()
            settings['freshclam_path'] = self.freshclam_path.text()
            settings['clamscan_path'] = self.clamscan_path.text()
        else:
            settings['clamd_path'] = ""
            settings['freshclam_path'] = ""
            settings['clamscan_path'] = ""

        # Get database settings
        settings['db_update_interval'] = self.db_update_interval.value()
        settings['db_mirror_url'] = self.db_mirror_url.text()
        settings['db_path'] = self.db_path_display.text()
        settings['scanner_type'] = self.scanner_type_combo.currentData()

        # Get scan settings
        if hasattr(self, 'default_scan_archives'):
            settings['scan_archives'] = self.default_scan_archives.isChecked()
        if hasattr(self, 'default_scan_heuristics'):
            settings['scan_heuristics'] = self.default_scan_heuristics.isChecked()
        if hasattr(self, 'default_scan_pua'):
            settings['scan_pua'] = self.default_scan_pua.isChecked()
        if hasattr(self, 'default_enable_quarantine'):
            settings['enable_quarantine'] = self.default_enable_quarantine.isChecked()
        if hasattr(self, 'default_max_file_size'):
            settings['max_file_size'] = self.default_max_file_size.text()
        if hasattr(self, 'default_max_scan_time'):
            settings['max_scan_time'] = self.default_max_scan_time.text()
        if hasattr(self, 'default_exclude_patterns'):
            settings['exclude_patterns'] = self.default_exclude_patterns.text()
        if hasattr(self, 'default_include_patterns'):
            settings['include_patterns'] = self.default_include_patterns.text()

        return settings

    def apply_settings(self, settings: Dict):
        """Apply settings to the form fields."""
        try:
            # Apply ClamAV paths (only if using ClamAV scanner)
            current_scanner_type = self.scanner_type_combo.currentData()
            if current_scanner_type == "clamav":
                if 'clamd_path' in settings:
                    self.clamd_path.setText(settings['clamd_path'])
                if 'freshclam_path' in settings:
                    self.freshclam_path.setText(settings['freshclam_path'])
                if 'clamscan_path' in settings:
                    self.clamscan_path.setText(settings['clamscan_path'])
            else:
                # Clear ClamAV paths when using integrated scanner
                self.clamd_path.clear()
                self.freshclam_path.clear()
                self.clamscan_path.clear()

            # Apply database settings
            if 'db_update_interval' in settings:
                self.db_update_interval.setValue(settings['db_update_interval'])
            if 'db_mirror_url' in settings:
                self.db_mirror_url.setText(settings['db_mirror_url'])
            if 'db_path' in settings:
                self.db_path_display.setText(settings['db_path'])

            # Apply scanner type
            if 'scanner_type' in settings:
                scanner_type = settings['scanner_type']
                if scanner_type == 'integrated':
                    self.scanner_type_combo.setCurrentText(self.tr("Integrated Scanner"))
                elif scanner_type == 'clamav':
                    self.scanner_type_combo.setCurrentText(self.tr("ClamAV Scanner"))

            # Apply scan settings
            if 'scan_archives' in settings and hasattr(self, 'default_scan_archives'):
                self.default_scan_archives.setChecked(settings['scan_archives'])
            if 'scan_heuristics' in settings and hasattr(self, 'default_scan_heuristics'):
                self.default_scan_heuristics.setChecked(settings['scan_heuristics'])
            if 'scan_pua' in settings and hasattr(self, 'default_scan_pua'):
                self.default_scan_pua.setChecked(settings['scan_pua'])
            if 'enable_quarantine' in settings and hasattr(self, 'default_enable_quarantine'):
                self.default_enable_quarantine.setChecked(settings['enable_quarantine'])
            if 'max_file_size' in settings and hasattr(self, 'default_max_file_size'):
                self.default_max_file_size.setText(str(settings['max_file_size']))
            if 'max_scan_time' in settings and hasattr(self, 'default_max_scan_time'):
                self.default_max_scan_time.setText(str(settings['max_scan_time']))
            if 'exclude_patterns' in settings and hasattr(self, 'default_exclude_patterns'):
                self.default_exclude_patterns.setText(settings['exclude_patterns'])
            if 'include_patterns' in settings and hasattr(self, 'default_include_patterns'):
                self.default_include_patterns.setText(settings['include_patterns'])

        except Exception as e:
            logger.error(f"Error applying settings: {e}")

    def tr(self, text):
        """Translate text (placeholder for translation system)."""
        if self.parent and hasattr(self.parent, 'tr'):
            return self.parent.tr(text)
        return text
