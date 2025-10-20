"""
Advanced scan settings dialog for ClamAV GUI.
"""
import os
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QPushButton, QCheckBox, QSpinBox, QLineEdit,
    QComboBox, QMessageBox, QTabWidget, QWidget
)


class ScanSettingsDialog(QDialog):
    """Advanced scan settings dialog."""

    def __init__(self, parent=None, current_settings=None):
        """Initialize the scan settings dialog.

        Args:
            parent: Parent widget
            current_settings: Current scan settings to load
        """
        super().__init__(parent)
        self.current_settings = current_settings or {}
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(self.tr("Advanced Scan Settings"))
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        # Create tab widget for different settings categories
        self.tab_widget = QTabWidget()

        # Basic scan options tab
        basic_tab = self.create_basic_tab()
        self.tab_widget.addTab(basic_tab, self.tr("Basic Options"))

        # Performance tab
        performance_tab = self.create_performance_tab()
        self.tab_widget.addTab(performance_tab, self.tr("Performance"))

        # File filtering tab
        filtering_tab = self.create_filtering_tab()
        self.tab_widget.addTab(filtering_tab, self.tr("File Filtering"))

        # Advanced options tab
        advanced_tab = self.create_advanced_tab()
        self.tab_widget.addTab(advanced_tab, self.tr("Advanced"))

        layout.addWidget(self.tab_widget)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.save_btn = QPushButton(self.tr("Save Settings"))
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setStyleSheet("""
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
        """)
        buttons_layout.addWidget(self.save_btn)

        self.reset_btn = QPushButton(self.tr("Reset to Defaults"))
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        self.reset_btn.setStyleSheet("""
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
        """)
        buttons_layout.addWidget(self.reset_btn)

        self.cancel_btn = QPushButton(self.tr("Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
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
        """)
        buttons_layout.addWidget(self.cancel_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

    def create_basic_tab(self):
        """Create the basic scan options tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Scan behavior group
        behavior_group = QGroupBox(self.tr("Scan Behavior"))
        behavior_layout = QVBoxLayout()

        self.scan_archives = QCheckBox(self.tr("Scan archives (zip, rar, 7z, etc.)"))
        self.scan_archives.setChecked(True)
        behavior_layout.addWidget(self.scan_archives)

        self.scan_mail = QCheckBox(self.tr("Scan email files (.eml, .msg)"))
        self.scan_mail.setChecked(True)
        behavior_layout.addWidget(self.scan_mail)

        self.scan_ole2 = QCheckBox(self.tr("Scan OLE2 containers (Office documents)"))
        self.scan_ole2.setChecked(True)
        behavior_layout.addWidget(self.scan_ole2)

        self.scan_pdf = QCheckBox(self.tr("Scan PDF documents"))
        self.scan_pdf.setChecked(True)
        behavior_layout.addWidget(self.scan_pdf)

        self.scan_html = QCheckBox(self.tr("Scan HTML and embedded scripts"))
        self.scan_html.setChecked(True)
        behavior_layout.addWidget(self.scan_html)

        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)

        # Threat detection group
        detection_group = QGroupBox(self.tr("Threat Detection"))
        detection_layout = QVBoxLayout()

        self.enable_heuristics = QCheckBox(self.tr("Enable heuristic analysis"))
        self.enable_heuristics.setChecked(True)
        detection_layout.addWidget(self.enable_heuristics)

        self.detect_pua = QCheckBox(self.tr("Detect potentially unwanted applications (PUA)"))
        self.detect_pua.setChecked(False)
        detection_layout.addWidget(self.detect_pua)

        self.scan_pe = QCheckBox(self.tr("Scan PE files (executables)"))
        self.scan_pe.setChecked(True)
        detection_layout.addWidget(self.scan_pe)

        self.scan_elf = QCheckBox(self.tr("Scan ELF files (Linux executables)"))
        self.scan_elf.setChecked(True)
        detection_layout.addWidget(self.scan_elf)

        detection_group.setLayout(detection_layout)
        layout.addWidget(detection_group)

        layout.addStretch()
        return tab

    def create_performance_tab(self):
        """Create the performance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Performance limits group
        limits_group = QGroupBox(self.tr("Performance Limits"))
        limits_layout = QFormLayout()

        self.max_filesize = QSpinBox()
        self.max_filesize.setRange(1, 10000)
        self.max_filesize.setValue(100)
        self.max_filesize.setSuffix(" MB")
        limits_layout.addRow(self.tr("Maximum file size:"), self.max_filesize)

        self.max_scantime = QSpinBox()
        self.max_scantime.setRange(1, 3600)
        self.max_scantime.setValue(300)
        self.max_scantime.setSuffix(" seconds")
        limits_layout.addRow(self.tr("Maximum scan time per file:"), self.max_scantime)

        self.max_recursion = QSpinBox()
        self.max_recursion.setRange(1, 50)
        self.max_recursion.setValue(16)
        limits_layout.addRow(self.tr("Maximum archive recursion depth:"), self.max_recursion)

        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)

        # Memory and CPU group
        resources_group = QGroupBox(self.tr("Resource Usage"))
        resources_layout = QVBoxLayout()

        self.low_priority = QCheckBox(self.tr("Run scans with low CPU priority"))
        self.low_priority.setChecked(False)
        resources_layout.addWidget(self.low_priority)

        self.parallel_scans = QCheckBox(self.tr("Enable parallel scanning (experimental)"))
        self.parallel_scans.setChecked(False)
        resources_layout.addWidget(self.parallel_scans)

        self.smart_scanning = QCheckBox(self.tr("Enable smart scanning (skip known safe files)"))
        self.smart_scanning.setChecked(True)
        resources_layout.addWidget(self.smart_scanning)

        resources_group.setLayout(resources_layout)
        layout.addWidget(resources_group)

        layout.addStretch()
        return tab

    def create_filtering_tab(self):
        """Create the file filtering tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Include patterns group
        include_group = QGroupBox(self.tr("Include Patterns"))
        include_layout = QVBoxLayout()

        self.include_all = QCheckBox(self.tr("Scan all files (ignore patterns)"))
        self.include_all.setChecked(False)
        include_layout.addWidget(self.include_all)

        include_layout.addWidget(QLabel(self.tr("File patterns to include (comma-separated):")))

        self.include_patterns = QLineEdit()
        self.include_patterns.setPlaceholderText("*.exe,*.dll,*.pdf,*.doc,*.docx,*.xls,*.xlsx")
        self.include_patterns.setText("*.exe,*.dll,*.pdf,*.doc,*.docx,*.xls,*.xlsx")
        include_layout.addWidget(self.include_patterns)

        include_group.setLayout(include_layout)
        layout.addWidget(include_group)

        # Exclude patterns group
        exclude_group = QGroupBox(self.tr("Exclude Patterns"))
        exclude_layout = QVBoxLayout()

        self.exclude_system = QCheckBox(self.tr("Exclude system directories"))
        self.exclude_system.setChecked(True)
        exclude_layout.addWidget(self.exclude_system)

        self.exclude_temp = QCheckBox(self.tr("Exclude temporary files"))
        self.exclude_temp.setChecked(True)
        exclude_layout.addWidget(self.exclude_temp)

        exclude_layout.addWidget(QLabel(self.tr("File patterns to exclude (comma-separated):")))

        self.exclude_patterns = QLineEdit()
        self.exclude_patterns.setPlaceholderText("*.log,*.tmp,*.cache,*.temp")
        self.exclude_patterns.setText("*.log,*.tmp,*.cache,*.temp")
        exclude_layout.addWidget(self.exclude_patterns)

        exclude_group.setLayout(exclude_layout)
        layout.addWidget(exclude_group)

        # Directory exclusions
        dir_group = QGroupBox(self.tr("Directory Exclusions"))
        dir_layout = QVBoxLayout()

        dir_layout.addWidget(QLabel(self.tr("Directories to exclude (one per line):")))

        self.exclude_dirs = QLineEdit()
        self.exclude_dirs.setPlaceholderText("/tmp\n/var/log\n/home/user/cache")
        dir_layout.addWidget(self.exclude_dirs)

        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        layout.addStretch()
        return tab

    def create_advanced_tab(self):
        """Create the advanced options tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Alert options group
        alert_group = QGroupBox(self.tr("Alert Options"))
        alert_layout = QVBoxLayout()

        self.alert_broken = QCheckBox(self.tr("Alert on broken executables"))
        self.alert_broken.setChecked(False)
        alert_layout.addWidget(self.alert_broken)

        self.alert_encrypted = QCheckBox(self.tr("Alert on encrypted archives"))
        self.alert_encrypted.setChecked(True)
        alert_layout.addWidget(self.alert_encrypted)

        self.alert_partition = QCheckBox(self.tr("Alert on partition intersections"))
        self.alert_partition.setChecked(False)
        alert_layout.addWidget(self.alert_partition)

        alert_group.setLayout(alert_layout)
        layout.addWidget(alert_group)

        # Output options group
        output_group = QGroupBox(self.tr("Output Options"))
        output_layout = QVBoxLayout()

        self.verbose_output = QCheckBox(self.tr("Verbose scan output"))
        self.verbose_output.setChecked(False)
        output_layout.addWidget(self.verbose_output)

        self.debug_output = QCheckBox(self.tr("Debug scan output"))
        self.debug_output.setChecked(False)
        output_layout.addWidget(self.debug_output)

        self.quiet_mode = QCheckBox(self.tr("Quiet mode (minimal output)"))
        self.quiet_mode.setChecked(False)
        output_layout.addWidget(self.quiet_mode)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Database options group
        db_group = QGroupBox(self.tr("Database Options"))
        db_layout = QVBoxLayout()

        self.official_db = QCheckBox(self.tr("Use official ClamAV database only"))
        self.official_db.setChecked(True)
        db_layout.addWidget(self.official_db)

        self.third_party_db = QCheckBox(self.tr("Include third-party signatures"))
        self.third_party_db.setChecked(False)
        db_layout.addWidget(self.third_party_db)

        db_layout.addWidget(QLabel(self.tr("Custom database directory:")))

        self.custom_db_dir = QLineEdit()
        self.custom_db_dir.setPlaceholderText("/usr/local/share/clamav")
        db_layout.addWidget(self.custom_db_dir)

        db_group.setLayout(db_layout)
        layout.addWidget(db_group)

        layout.addStretch()
        return tab

    def load_settings(self):
        """Load current settings into the dialog."""
        # Basic options
        self.scan_archives.setChecked(self.current_settings.get('scan_archives', True))
        self.scan_mail.setChecked(self.current_settings.get('scan_mail', True))
        self.scan_ole2.setChecked(self.current_settings.get('scan_ole2', True))
        self.scan_pdf.setChecked(self.current_settings.get('scan_pdf', True))
        self.scan_html.setChecked(self.current_settings.get('scan_html', True))
        self.enable_heuristics.setChecked(self.current_settings.get('enable_heuristics', True))
        self.detect_pua.setChecked(self.current_settings.get('detect_pua', False))
        self.scan_pe.setChecked(self.current_settings.get('scan_pe', True))
        self.scan_elf.setChecked(self.current_settings.get('scan_elf', True))

        # Performance options
        self.max_filesize.setValue(self.current_settings.get('max_filesize', 100))
        self.max_scantime.setValue(self.current_settings.get('max_scantime', 300))
        self.max_recursion.setValue(self.current_settings.get('max_recursion', 16))
        self.low_priority.setChecked(self.current_settings.get('low_priority', False))
        self.parallel_scans.setChecked(self.current_settings.get('parallel_scans', False))
        self.smart_scanning.setChecked(self.current_settings.get('smart_scanning', True))

        # Filtering options
        self.include_all.setChecked(self.current_settings.get('include_all', False))
        self.include_patterns.setText(self.current_settings.get('include_patterns', '*.exe,*.dll,*.pdf,*.doc,*.docx,*.xls,*.xlsx'))
        self.exclude_system.setChecked(self.current_settings.get('exclude_system', True))
        self.exclude_temp.setChecked(self.current_settings.get('exclude_temp', True))
        self.exclude_patterns.setText(self.current_settings.get('exclude_patterns', '*.log,*.tmp,*.cache,*.temp'))
        self.exclude_dirs.setText(self.current_settings.get('exclude_dirs', ''))

        # Advanced options
        self.alert_broken.setChecked(self.current_settings.get('alert_broken', False))
        self.alert_encrypted.setChecked(self.current_settings.get('alert_encrypted', True))
        self.alert_partition.setChecked(self.current_settings.get('alert_partition', False))
        self.verbose_output.setChecked(self.current_settings.get('verbose_output', False))
        self.debug_output.setChecked(self.current_settings.get('debug_output', False))
        self.quiet_mode.setChecked(self.current_settings.get('quiet_mode', False))
        self.official_db.setChecked(self.current_settings.get('official_db', True))
        self.third_party_db.setChecked(self.current_settings.get('third_party_db', False))
        self.custom_db_dir.setText(self.current_settings.get('custom_db_dir', ''))

    def save_settings(self):
        """Save the settings and close dialog."""
        # Collect all settings
        settings = {
            # Basic options
            'scan_archives': self.scan_archives.isChecked(),
            'scan_mail': self.scan_mail.isChecked(),
            'scan_ole2': self.scan_ole2.isChecked(),
            'scan_pdf': self.scan_pdf.isChecked(),
            'scan_html': self.scan_html.isChecked(),
            'enable_heuristics': self.enable_heuristics.isChecked(),
            'detect_pua': self.detect_pua.isChecked(),
            'scan_pe': self.scan_pe.isChecked(),
            'scan_elf': self.scan_elf.isChecked(),

            # Performance options
            'max_filesize': self.max_filesize.value(),
            'max_scantime': self.max_scantime.value(),
            'max_recursion': self.max_recursion.value(),
            'low_priority': self.low_priority.isChecked(),
            'parallel_scans': self.parallel_scans.isChecked(),
            'smart_scanning': self.smart_scanning.isChecked(),

            # Filtering options
            'include_all': self.include_all.isChecked(),
            'include_patterns': self.include_patterns.text(),
            'exclude_system': self.exclude_system.isChecked(),
            'exclude_temp': self.exclude_temp.isChecked(),
            'exclude_patterns': self.exclude_patterns.text(),
            'exclude_dirs': self.exclude_dirs.text(),

            # Advanced options
            'alert_broken': self.alert_broken.isChecked(),
            'alert_encrypted': self.alert_encrypted.isChecked(),
            'alert_partition': self.alert_partition.isChecked(),
            'verbose_output': self.verbose_output.isChecked(),
            'debug_output': self.debug_output.isChecked(),
            'quiet_mode': self.quiet_mode.isChecked(),
            'official_db': self.official_db.isChecked(),
            'third_party_db': self.third_party_db.isChecked(),
            'custom_db_dir': self.custom_db_dir.text(),
        }

        # Emit settings to parent
        if hasattr(self.parent(), 'scan_settings_updated'):
            self.parent().scan_settings_updated.emit(settings)

        self.accept()

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self, self.tr("Reset Settings"),
            self.tr("Are you sure you want to reset all settings to defaults?\n\nThis action cannot be undone."),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Set default values
            self.scan_archives.setChecked(True)
            self.scan_mail.setChecked(True)
            self.scan_ole2.setChecked(True)
            self.scan_pdf.setChecked(True)
            self.scan_html.setChecked(True)
            self.enable_heuristics.setChecked(True)
            self.detect_pua.setChecked(False)
            self.scan_pe.setChecked(True)
            self.scan_elf.setChecked(True)

            self.max_filesize.setValue(100)
            self.max_scantime.setValue(300)
            self.max_recursion.setValue(16)
            self.low_priority.setChecked(False)
            self.parallel_scans.setChecked(False)
            self.smart_scanning.setChecked(True)

            self.include_all.setChecked(False)
            self.include_patterns.setText("*.exe,*.dll,*.pdf,*.doc,*.docx,*.xls,*.xlsx")
            self.exclude_system.setChecked(True)
            self.exclude_temp.setChecked(True)
            self.exclude_patterns.setText("*.log,*.tmp,*.cache,*.temp")
            self.exclude_dirs.clear()

            self.alert_broken.setChecked(False)
            self.alert_encrypted.setChecked(True)
            self.alert_partition.setChecked(False)
            self.verbose_output.setChecked(False)
            self.debug_output.setChecked(False)
            self.quiet_mode.setChecked(False)
            self.official_db.setChecked(True)
            self.third_party_db.setChecked(False)
            self.custom_db_dir.clear()
